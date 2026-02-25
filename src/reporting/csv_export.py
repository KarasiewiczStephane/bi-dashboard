"""CSV export utilities.

Provides functions to export filtered dashboard data as CSV for
download via the Dash ``dcc.Download`` component.
"""

import io
from datetime import date
from typing import Optional

import pandas as pd

from src.data.queries import QueryLayer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CSVExporter:
    """Export filtered dashboard data as CSV.

    Args:
        query_layer: Optional QueryLayer instance.
    """

    def __init__(self, query_layer: Optional[QueryLayer] = None) -> None:
        self._ql = query_layer or QueryLayer()

    def export_sales_summary(
        self,
        start_date: date,
        end_date: date,
        region: Optional[str] = None,
    ) -> str:
        """Export a combined sales summary as CSV text.

        Includes KPIs, revenue by region, and revenue by category
        in a single CSV output.

        Args:
            start_date: Start of date range.
            end_date: End of date range.
            region: Optional region filter.

        Returns:
            CSV-formatted string.
        """
        buf = io.StringIO()

        # KPIs section
        kpis = self._ql.get_kpis(start_date, end_date, region=region)
        kpi_df = pd.DataFrame([{"metric": k, "value": v} for k, v in kpis.items()])
        buf.write("# KPI Summary\n")
        kpi_df.to_csv(buf, index=False)
        buf.write("\n")

        # Revenue by region
        region_df = self._ql.get_revenue_by_region(start_date, end_date)
        buf.write("# Revenue by Region\n")
        region_df.to_csv(buf, index=False)
        buf.write("\n")

        # Revenue by category
        cat_df = self._ql.get_revenue_by_category(start_date, end_date, region=region)
        buf.write("# Revenue by Category\n")
        cat_df.to_csv(buf, index=False)

        logger.info("CSV export generated for %s to %s", start_date, end_date)
        return buf.getvalue()

    def export_dataframe(self, df: pd.DataFrame) -> str:
        """Convert any DataFrame to CSV text.

        Args:
            df: The DataFrame to export.

        Returns:
            CSV-formatted string.
        """
        return df.to_csv(index=False)
