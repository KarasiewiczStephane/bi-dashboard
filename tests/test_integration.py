"""Integration tests for the full dashboard pipeline.

Tests the callback logic directly by calling the inner functions
that Dash would normally invoke, ensuring end-to-end data flow.
"""

from datetime import date
from pathlib import Path

import plotly.graph_objects as go
import pytest

from src.dashboard.callbacks import _parse_date
from src.dashboard.components.charts import _empty_figure
from src.dashboard.components.kpi_cards import create_kpi_section
from src.dashboard.roles import filter_kpis, get_permissions
from src.data.database import Database
from src.data.generator import DataGenerator
from src.data.queries import QueryLayer
from src.reporting.csv_export import CSVExporter
from src.reporting.pdf_generator import PDFReportGenerator


@pytest.fixture(scope="module")
def populated_db(tmp_path_factory: pytest.TempPathFactory) -> Database:
    """Create a temp DB with full pipeline data."""
    db_path = str(tmp_path_factory.mktemp("integ") / "test.duckdb")
    database = Database(db_path=db_path)
    database.initialize_schema()
    database.create_indexes()
    gen = DataGenerator(seed=42, database=database)
    gen.generate_all(transaction_count=1000)
    return database


@pytest.fixture()
def ql(populated_db: Database) -> QueryLayer:
    return QueryLayer(database=populated_db)


class TestEndToEndPipeline:
    """Test the full data → query → chart → export pipeline."""

    def test_kpi_to_cards(self, ql: QueryLayer) -> None:
        kpis = ql.get_kpis(date(2022, 1, 1), date(2024, 12, 31))
        section = create_kpi_section(kpis)
        assert len(section.children) == 4

    def test_filtered_kpis_for_viewer(self, ql: QueryLayer) -> None:
        kpis = ql.get_kpis(date(2022, 1, 1), date(2024, 12, 31))
        filtered = filter_kpis(kpis, "Viewer")
        section = create_kpi_section(filtered)
        assert section is not None

    def test_manager_region_restriction(self, ql: QueryLayer) -> None:
        perms = get_permissions("Manager")
        region = perms["assigned_region"]
        kpis = ql.get_kpis(date(2022, 1, 1), date(2024, 12, 31), region=region)
        assert kpis["total_revenue"] > 0

    def test_csv_then_pdf(self, ql: QueryLayer, tmp_path: Path) -> None:
        csv_exp = CSVExporter(query_layer=ql)
        csv_text = csv_exp.export_sales_summary(date(2023, 1, 1), date(2023, 12, 31))
        assert "total_revenue" in csv_text

        pdf_gen = PDFReportGenerator(query_layer=ql)
        pdf_gen._output_dir = tmp_path
        pdf_path = pdf_gen.generate_weekly_report(end_date=date(2023, 6, 30))
        assert pdf_path.exists()

    def test_full_date_range_queries(self, ql: QueryLayer) -> None:
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)

        region_df = ql.get_revenue_by_region(start, end)
        assert not region_df.empty

        cat_df = ql.get_revenue_by_category(start, end)
        assert not cat_df.empty

        ts_df = ql.get_revenue_time_series(start, end, granularity="quarter")
        assert not ts_df.empty

        cohort_df = ql.get_cohort_data(start, end)
        assert not cohort_df.empty

        funnel = ql.get_funnel_data(start, end)
        assert len(funnel) == 5


class TestCallbackHelpers:
    """Test callback helper functions directly."""

    def test_parse_date_various_formats(self) -> None:
        assert _parse_date("2023-01-15") == date(2023, 1, 15)
        assert _parse_date("2023-06-01T10:30:00") == date(2023, 6, 1)
        assert _parse_date(date(2024, 3, 1)) == date(2024, 3, 1)

    def test_empty_figure_has_annotation(self) -> None:
        fig = _empty_figure("No data")
        assert isinstance(fig, go.Figure)
        assert len(fig.layout.annotations) == 1

    def test_drilldown_disabled_for_viewer(self) -> None:
        perms = get_permissions("Viewer")
        assert not perms["drilldown_enabled"]
        fig = _empty_figure("Drill-down disabled for your role")
        assert isinstance(fig, go.Figure)


class TestMainModule:
    """Verify main module can be imported."""

    def test_main_importable(self) -> None:
        from src.main import main

        assert callable(main)
