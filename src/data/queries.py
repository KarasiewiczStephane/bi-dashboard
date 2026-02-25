"""SQL query layer for the BI Dashboard.

Provides parameterized queries for KPI calculations, revenue breakdowns,
cohort analysis, funnel metrics, and drill-down aggregations.
"""

from datetime import date, timedelta
from typing import Any, Optional

import pandas as pd

from src.data.database import Database, db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryLayer:
    """Parameterized SQL queries for all dashboard data needs.

    Args:
        database: Optional Database instance; defaults to the module singleton.
    """

    def __init__(self, database: Optional[Database] = None) -> None:
        self._db = database or db

    # ------------------------------------------------------------------
    # KPI queries
    # ------------------------------------------------------------------

    def get_kpis(
        self,
        start_date: date,
        end_date: date,
        region: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return all KPI values for the given date range.

        Args:
            start_date: Inclusive start date.
            end_date: Inclusive end date.
            region: If provided, restrict to this region.

        Returns:
            Dict with keys: total_revenue, prev_revenue, revenue_change_pct,
            customer_count, new_customers, avg_order_value, transaction_count.
        """
        region_clause = "AND region = ?" if region else ""
        params: list[Any] = [start_date, end_date]
        if region:
            params.append(region)

        with self._db.get_connection() as conn:
            row = conn.execute(
                f"""
                SELECT
                    COALESCE(SUM(amount), 0) AS total_revenue,
                    COUNT(*) AS transaction_count,
                    COUNT(DISTINCT customer_id) AS customer_count,
                    COALESCE(AVG(amount), 0) AS avg_order_value
                FROM fact_sales
                WHERE date BETWEEN ? AND ? {region_clause}
                """,
                params,
            ).fetchone()

            total_revenue = float(row[0])
            transaction_count = int(row[1])
            customer_count = int(row[2])
            avg_order_value = float(row[3])

            # Previous period for comparison
            period_days = (end_date - start_date).days
            prev_start = start_date - timedelta(days=period_days + 1)
            prev_end = start_date - timedelta(days=1)
            prev_params: list[Any] = [prev_start, prev_end]
            if region:
                prev_params.append(region)

            prev_revenue = float(
                conn.execute(
                    f"""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM fact_sales
                    WHERE date BETWEEN ? AND ? {region_clause}
                    """,
                    prev_params,
                ).fetchone()[0]
            )

            # New customers (signed up in the period)
            cust_params: list[Any] = [
                start_date,
                end_date,
                start_date,
                end_date,
            ]
            if region:
                cust_params.append(region)

            new_customers = int(
                conn.execute(
                    f"""
                    SELECT COUNT(DISTINCT s.customer_id)
                    FROM fact_sales s
                    JOIN dim_customer c
                        ON s.customer_id = c.customer_id
                    WHERE s.date BETWEEN ? AND ?
                      AND c.signup_date BETWEEN ? AND ?
                      {region_clause.replace("region", "s.region")}
                    """,
                    cust_params,
                ).fetchone()[0]
            )

        change_pct = (
            ((total_revenue - prev_revenue) / prev_revenue * 100)
            if prev_revenue
            else 0.0
        )

        return {
            "total_revenue": total_revenue,
            "prev_revenue": prev_revenue,
            "revenue_change_pct": round(change_pct, 2),
            "customer_count": customer_count,
            "new_customers": new_customers,
            "avg_order_value": round(avg_order_value, 2),
            "transaction_count": transaction_count,
        }

    # ------------------------------------------------------------------
    # Revenue breakdowns
    # ------------------------------------------------------------------

    def get_revenue_by_region(
        self,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Revenue aggregated by region.

        Args:
            start_date: Inclusive start.
            end_date: Inclusive end.

        Returns:
            DataFrame with columns: region, revenue, transaction_count.
        """
        with self._db.get_connection() as conn:
            return conn.execute(
                """
                SELECT
                    region,
                    SUM(amount) AS revenue,
                    COUNT(*) AS transaction_count
                FROM fact_sales
                WHERE date BETWEEN ? AND ?
                GROUP BY region
                ORDER BY revenue DESC
                """,
                [start_date, end_date],
            ).fetchdf()

    def get_revenue_by_category(
        self,
        start_date: date,
        end_date: date,
        region: Optional[str] = None,
    ) -> pd.DataFrame:
        """Revenue by product category.

        Args:
            start_date: Inclusive start.
            end_date: Inclusive end.
            region: Optional region filter.

        Returns:
            DataFrame with columns: category, revenue, units_sold.
        """
        region_clause = "AND s.region = ?" if region else ""
        params: list[Any] = [start_date, end_date]
        if region:
            params.append(region)

        with self._db.get_connection() as conn:
            return conn.execute(
                f"""
                SELECT
                    p.category,
                    SUM(s.amount) AS revenue,
                    SUM(s.quantity) AS units_sold
                FROM fact_sales s
                JOIN dim_product p ON s.product_id = p.product_id
                WHERE s.date BETWEEN ? AND ? {region_clause}
                GROUP BY p.category
                ORDER BY revenue DESC
                """,
                params,
            ).fetchdf()

    def get_revenue_by_product(
        self,
        start_date: date,
        end_date: date,
        category: str,
    ) -> pd.DataFrame:
        """Revenue drill-down by product within a category.

        Args:
            start_date: Inclusive start.
            end_date: Inclusive end.
            category: Product category to drill into.

        Returns:
            DataFrame with columns: product_id, name, revenue, units_sold.
        """
        with self._db.get_connection() as conn:
            return conn.execute(
                """
                SELECT
                    p.product_id,
                    p.name,
                    SUM(s.amount) AS revenue,
                    SUM(s.quantity) AS units_sold
                FROM fact_sales s
                JOIN dim_product p ON s.product_id = p.product_id
                WHERE s.date BETWEEN ? AND ?
                  AND p.category = ?
                GROUP BY p.product_id, p.name
                ORDER BY revenue DESC
                """,
                [start_date, end_date, category],
            ).fetchdf()

    # ------------------------------------------------------------------
    # Cohort analysis
    # ------------------------------------------------------------------

    def get_cohort_data(
        self,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Return cohort retention heatmap data.

        Args:
            start_date: Inclusive start.
            end_date: Inclusive end.

        Returns:
            DataFrame with columns: cohort_month, activity_month,
            active_customers, revenue.
        """
        with self._db.get_connection() as conn:
            return conn.execute(
                """
                SELECT
                    DATE_TRUNC('month', c.signup_date) AS cohort_month,
                    DATE_TRUNC('month', s.date) AS activity_month,
                    COUNT(DISTINCT s.customer_id) AS active_customers,
                    SUM(s.amount) AS revenue
                FROM fact_sales s
                JOIN dim_customer c ON s.customer_id = c.customer_id
                WHERE s.date BETWEEN ? AND ?
                GROUP BY
                    DATE_TRUNC('month', c.signup_date),
                    DATE_TRUNC('month', s.date)
                ORDER BY cohort_month, activity_month
                """,
                [start_date, end_date],
            ).fetchdf()

    # ------------------------------------------------------------------
    # Time series
    # ------------------------------------------------------------------

    def get_revenue_time_series(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "month",
        region: Optional[str] = None,
    ) -> pd.DataFrame:
        """Revenue time series at the requested granularity.

        Args:
            start_date: Inclusive start.
            end_date: Inclusive end.
            granularity: One of 'day', 'week', 'month', 'quarter', 'year'.
            region: Optional region filter.

        Returns:
            DataFrame with columns: period, revenue, transaction_count.
        """
        trunc_map = {
            "day": "day",
            "week": "week",
            "month": "month",
            "quarter": "quarter",
            "year": "year",
        }
        trunc = trunc_map.get(granularity, "month")
        region_clause = "AND region = ?" if region else ""
        params: list[Any] = [start_date, end_date]
        if region:
            params.append(region)

        with self._db.get_connection() as conn:
            return conn.execute(
                f"""
                SELECT
                    DATE_TRUNC('{trunc}', date) AS period,
                    SUM(amount) AS revenue,
                    COUNT(*) AS transaction_count
                FROM fact_sales
                WHERE date BETWEEN ? AND ? {region_clause}
                GROUP BY DATE_TRUNC('{trunc}', date)
                ORDER BY period
                """,
                params,
            ).fetchdf()

    # ------------------------------------------------------------------
    # Funnel data
    # ------------------------------------------------------------------

    def get_funnel_data(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Simulated sales funnel metrics.

        Args:
            start_date: Inclusive start.
            end_date: Inclusive end.

        Returns:
            List of dicts with keys: stage, count.
        """
        with self._db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT customer_id) AS purchasers,
                    COUNT(*) AS purchases
                FROM fact_sales
                WHERE date BETWEEN ? AND ?
                """,
                [start_date, end_date],
            ).fetchone()

        purchasers = int(row[0])
        purchases = int(row[1])
        # Simulated funnel ratios
        return [
            {"stage": "Awareness", "count": purchasers * 5},
            {"stage": "Consideration", "count": purchasers * 3},
            {"stage": "Intent", "count": purchasers * 2},
            {"stage": "Purchase", "count": purchasers},
            {"stage": "Repeat", "count": purchases - purchasers},
        ]


query_layer = QueryLayer()
