"""Tests for the SQL query layer."""

from datetime import date

import pandas as pd
import pytest

from src.data.database import Database
from src.data.generator import DataGenerator
from src.data.queries import QueryLayer


@pytest.fixture(scope="module")
def populated_db(tmp_path_factory: pytest.TempPathFactory) -> Database:
    """Create a temp DB with schema + sample data (shared across module)."""
    db_path = str(tmp_path_factory.mktemp("query") / "test.duckdb")
    database = Database(db_path=db_path)
    database.initialize_schema()
    gen = DataGenerator(seed=42, database=database)
    gen.generate_all(transaction_count=1000)
    return database


@pytest.fixture()
def ql(populated_db: Database) -> QueryLayer:
    """Return a QueryLayer wired to the populated DB."""
    return QueryLayer(database=populated_db)


class TestGetKPIs:
    """Verify KPI calculations."""

    def test_returns_all_keys(self, ql: QueryLayer) -> None:
        kpis = ql.get_kpis(date(2022, 1, 1), date(2024, 12, 31))
        expected_keys = {
            "total_revenue",
            "prev_revenue",
            "revenue_change_pct",
            "customer_count",
            "new_customers",
            "avg_order_value",
            "transaction_count",
        }
        assert expected_keys == set(kpis.keys())

    def test_revenue_positive(self, ql: QueryLayer) -> None:
        kpis = ql.get_kpis(date(2022, 1, 1), date(2024, 12, 31))
        assert kpis["total_revenue"] > 0

    def test_region_filter(self, ql: QueryLayer) -> None:
        all_kpis = ql.get_kpis(date(2022, 1, 1), date(2024, 12, 31))
        region_kpis = ql.get_kpis(date(2022, 1, 1), date(2024, 12, 31), region="North")
        assert region_kpis["total_revenue"] <= all_kpis["total_revenue"]

    def test_change_pct_calculated(self, ql: QueryLayer) -> None:
        kpis = ql.get_kpis(date(2023, 1, 1), date(2023, 6, 30))
        assert isinstance(kpis["revenue_change_pct"], float)


class TestRevenueByRegion:
    """Verify region revenue breakdown."""

    def test_returns_dataframe(self, ql: QueryLayer) -> None:
        df = ql.get_revenue_by_region(date(2022, 1, 1), date(2024, 12, 31))
        assert isinstance(df, pd.DataFrame)
        assert "region" in df.columns
        assert "revenue" in df.columns

    def test_all_regions_present(self, ql: QueryLayer) -> None:
        df = ql.get_revenue_by_region(date(2022, 1, 1), date(2024, 12, 31))
        assert len(df) > 0


class TestRevenueByCategory:
    """Verify category revenue breakdown."""

    def test_returns_dataframe(self, ql: QueryLayer) -> None:
        df = ql.get_revenue_by_category(date(2022, 1, 1), date(2024, 12, 31))
        assert isinstance(df, pd.DataFrame)
        assert "category" in df.columns

    def test_with_region_filter(self, ql: QueryLayer) -> None:
        df = ql.get_revenue_by_category(
            date(2022, 1, 1), date(2024, 12, 31), region="East"
        )
        assert isinstance(df, pd.DataFrame)


class TestRevenueByProduct:
    """Verify product drill-down."""

    def test_returns_products(self, ql: QueryLayer) -> None:
        df = ql.get_revenue_by_product(
            date(2022, 1, 1), date(2024, 12, 31), category="Electronics"
        )
        assert isinstance(df, pd.DataFrame)
        assert "name" in df.columns


class TestCohortData:
    """Verify cohort analysis query."""

    def test_returns_cohort_dataframe(self, ql: QueryLayer) -> None:
        df = ql.get_cohort_data(date(2022, 1, 1), date(2024, 12, 31))
        assert isinstance(df, pd.DataFrame)
        assert "cohort_month" in df.columns
        assert "active_customers" in df.columns


class TestTimeSeries:
    """Verify time series query."""

    def test_monthly(self, ql: QueryLayer) -> None:
        df = ql.get_revenue_time_series(
            date(2022, 1, 1), date(2024, 12, 31), granularity="month"
        )
        assert isinstance(df, pd.DataFrame)
        assert "period" in df.columns

    def test_with_region(self, ql: QueryLayer) -> None:
        df = ql.get_revenue_time_series(
            date(2022, 1, 1),
            date(2024, 12, 31),
            granularity="quarter",
            region="South",
        )
        assert isinstance(df, pd.DataFrame)


class TestFunnelData:
    """Verify funnel metrics."""

    def test_returns_stages(self, ql: QueryLayer) -> None:
        funnel = ql.get_funnel_data(date(2022, 1, 1), date(2024, 12, 31))
        assert len(funnel) == 5
        stages = [f["stage"] for f in funnel]
        assert "Awareness" in stages
        assert "Purchase" in stages

    def test_decreasing_funnel(self, ql: QueryLayer) -> None:
        funnel = ql.get_funnel_data(date(2022, 1, 1), date(2024, 12, 31))
        assert funnel[0]["count"] >= funnel[3]["count"]
