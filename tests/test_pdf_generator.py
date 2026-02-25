"""Tests for PDF report generation."""

from datetime import date
from pathlib import Path

import pytest

from src.data.database import Database
from src.data.generator import DataGenerator
from src.data.queries import QueryLayer
from src.reporting.pdf_generator import PDFReportGenerator


@pytest.fixture(scope="module")
def populated_db(tmp_path_factory: pytest.TempPathFactory) -> Database:
    """Create a temp DB with schema + sample data."""
    db_path = str(tmp_path_factory.mktemp("pdf") / "test.duckdb")
    database = Database(db_path=db_path)
    database.initialize_schema()
    gen = DataGenerator(seed=42, database=database)
    gen.generate_all(transaction_count=500)
    return database


@pytest.fixture()
def pdf_gen(populated_db: Database, tmp_path: Path) -> PDFReportGenerator:
    """Return a PDF generator wired to the temp DB."""
    ql = QueryLayer(database=populated_db)
    gen = PDFReportGenerator(query_layer=ql)
    gen._output_dir = tmp_path
    return gen


class TestWeeklyReport:
    """Verify PDF report file generation."""

    def test_creates_file(self, pdf_gen: PDFReportGenerator) -> None:
        path = pdf_gen.generate_weekly_report(end_date=date(2023, 6, 30))
        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.stat().st_size > 0

    def test_with_region(self, pdf_gen: PDFReportGenerator) -> None:
        path = pdf_gen.generate_weekly_report(
            end_date=date(2023, 6, 30), region="North"
        )
        assert path.exists()


class TestBufferGeneration:
    """Verify in-memory PDF generation."""

    def test_returns_bytes(self, pdf_gen: PDFReportGenerator) -> None:
        data = pdf_gen.generate_to_buffer(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
        )
        assert isinstance(data, bytes)
        assert len(data) > 0
        assert data[:5] == b"%PDF-"

    def test_with_region_filter(self, pdf_gen: PDFReportGenerator) -> None:
        data = pdf_gen.generate_to_buffer(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            region="South",
        )
        assert data[:5] == b"%PDF-"
