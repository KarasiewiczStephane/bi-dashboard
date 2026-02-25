"""Tests for CSV export functionality."""

from datetime import date

import pandas as pd
import pytest

from src.data.database import Database
from src.data.generator import DataGenerator
from src.data.queries import QueryLayer
from src.reporting.csv_export import CSVExporter


@pytest.fixture(scope="module")
def populated_db(tmp_path_factory: pytest.TempPathFactory) -> Database:
    """Create a temp DB with schema + sample data."""
    db_path = str(tmp_path_factory.mktemp("csv") / "test.duckdb")
    database = Database(db_path=db_path)
    database.initialize_schema()
    gen = DataGenerator(seed=42, database=database)
    gen.generate_all(transaction_count=500)
    return database


@pytest.fixture()
def exporter(populated_db: Database) -> CSVExporter:
    """Return a CSVExporter wired to the temp DB."""
    ql = QueryLayer(database=populated_db)
    return CSVExporter(query_layer=ql)


class TestExportSalesSummary:
    """Verify combined CSV export."""

    def test_returns_string(self, exporter: CSVExporter) -> None:
        csv = exporter.export_sales_summary(date(2022, 1, 1), date(2024, 12, 31))
        assert isinstance(csv, str)
        assert len(csv) > 0

    def test_contains_sections(self, exporter: CSVExporter) -> None:
        csv = exporter.export_sales_summary(date(2022, 1, 1), date(2024, 12, 31))
        assert "# KPI Summary" in csv
        assert "# Revenue by Region" in csv
        assert "# Revenue by Category" in csv

    def test_with_region_filter(self, exporter: CSVExporter) -> None:
        csv = exporter.export_sales_summary(
            date(2022, 1, 1), date(2024, 12, 31), region="North"
        )
        assert len(csv) > 0


class TestExportDataFrame:
    """Verify raw DataFrame CSV export."""

    def test_returns_csv(self, exporter: CSVExporter) -> None:
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        csv = exporter.export_dataframe(df)
        assert "a,b" in csv
        assert "1,3" in csv
