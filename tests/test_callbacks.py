"""Tests for dashboard callbacks."""

from datetime import date

import pytest

from src.dashboard.callbacks import _parse_date
from src.data.database import Database
from src.data.generator import DataGenerator
from src.data.queries import QueryLayer


class TestParseDate:
    """Verify date parsing helper."""

    def test_from_string(self) -> None:
        assert _parse_date("2023-06-15") == date(2023, 6, 15)

    def test_from_iso_with_time(self) -> None:
        assert _parse_date("2023-06-15T00:00:00") == date(2023, 6, 15)

    def test_from_date(self) -> None:
        assert _parse_date(date(2023, 1, 1)) == date(2023, 1, 1)


class TestCallbackRegistration:
    """Verify callbacks get registered on the app."""

    def test_registers_without_error(self) -> None:
        from src.dashboard.app import create_app

        app = create_app()
        assert len(app.callback_map) >= 3


class TestUpdateDashboard:
    """Test the main update callback logic indirectly via QueryLayer."""

    @pytest.fixture(scope="class")
    def ql_populated(self, tmp_path_factory: pytest.TempPathFactory) -> QueryLayer:
        db_path = str(tmp_path_factory.mktemp("cb") / "test.duckdb")
        database = Database(db_path=db_path)
        database.initialize_schema()
        gen = DataGenerator(seed=42, database=database)
        gen.generate_all(transaction_count=500)
        return QueryLayer(database=database)

    def test_kpis_returned(self, ql_populated: QueryLayer) -> None:
        kpis = ql_populated.get_kpis(date(2022, 1, 1), date(2024, 12, 31))
        assert kpis["total_revenue"] > 0

    def test_region_chart_data(self, ql_populated: QueryLayer) -> None:
        df = ql_populated.get_revenue_by_region(date(2022, 1, 1), date(2024, 12, 31))
        assert not df.empty

    def test_category_chart_data(self, ql_populated: QueryLayer) -> None:
        df = ql_populated.get_revenue_by_category(date(2022, 1, 1), date(2024, 12, 31))
        assert not df.empty

    def test_timeseries_data(self, ql_populated: QueryLayer) -> None:
        df = ql_populated.get_revenue_time_series(
            date(2022, 1, 1), date(2024, 12, 31), granularity="month"
        )
        assert not df.empty

    def test_cohort_data(self, ql_populated: QueryLayer) -> None:
        df = ql_populated.get_cohort_data(date(2022, 1, 1), date(2024, 12, 31))
        assert not df.empty

    def test_funnel_data(self, ql_populated: QueryLayer) -> None:
        funnel = ql_populated.get_funnel_data(date(2022, 1, 1), date(2024, 12, 31))
        assert len(funnel) == 5
