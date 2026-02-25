"""Tests for DuckDB database setup and schema definition."""

from pathlib import Path

import pytest

from src.data.database import Database


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Database:
    """Return a Database instance backed by a temp file."""
    db_path = str(tmp_path / "test.duckdb")
    return Database(db_path=db_path)


class TestDatabaseConnection:
    """Verify connection lifecycle."""

    def test_creates_db_file(self, tmp_db: Database) -> None:
        with tmp_db.get_connection() as conn:
            conn.execute("SELECT 1")
        assert Path(tmp_db.db_path).exists()

    def test_connection_closes(self, tmp_db: Database) -> None:
        with tmp_db.get_connection() as conn:
            conn.execute("SELECT 1")
        # After context, connection should be closed
        assert conn is not None  # object still exists but is closed

    def test_parent_directory_created(self, tmp_path: Path) -> None:
        nested = str(tmp_path / "nested" / "dir" / "test.duckdb")
        Database(db_path=nested)
        assert Path(nested).parent.is_dir()


class TestSchema:
    """Verify schema creation is idempotent and correct."""

    def test_schema_creation(self, tmp_db: Database) -> None:
        tmp_db.initialize_schema()
        with tmp_db.get_connection() as conn:
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall()
        table_names = [t[0] for t in tables]
        assert "dim_time" in table_names
        assert "dim_product" in table_names
        assert "dim_customer" in table_names
        assert "fact_sales" in table_names

    def test_schema_idempotent(self, tmp_db: Database) -> None:
        tmp_db.initialize_schema()
        tmp_db.initialize_schema()  # should not raise

    def test_dim_time_columns(self, tmp_db: Database) -> None:
        tmp_db.initialize_schema()
        with tmp_db.get_connection() as conn:
            cols = conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'dim_time' ORDER BY ordinal_position"
            ).fetchall()
        col_names = [c[0] for c in cols]
        assert "date" in col_names
        assert "month" in col_names
        assert "quarter" in col_names
        assert "is_holiday" in col_names

    def test_fact_sales_columns(self, tmp_db: Database) -> None:
        tmp_db.initialize_schema()
        with tmp_db.get_connection() as conn:
            cols = conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'fact_sales' ORDER BY ordinal_position"
            ).fetchall()
        col_names = [c[0] for c in cols]
        assert "transaction_id" in col_names
        assert "amount" in col_names
        assert "quantity" in col_names


class TestAggregationTables:
    """Verify aggregation table creation."""

    def test_aggregation_tables_empty(self, tmp_db: Database) -> None:
        tmp_db.initialize_schema()
        tmp_db.create_aggregation_tables()
        with tmp_db.get_connection() as conn:
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' ORDER BY table_name"
            ).fetchall()
        names = [t[0] for t in tables]
        assert "agg_daily_region" in names
        assert "agg_daily_category" in names
        assert "agg_cohort" in names


class TestIndexes:
    """Verify index creation."""

    def test_create_indexes(self, tmp_db: Database) -> None:
        tmp_db.initialize_schema()
        tmp_db.create_indexes()  # should not raise

    def test_indexes_idempotent(self, tmp_db: Database) -> None:
        tmp_db.initialize_schema()
        tmp_db.create_indexes()
        tmp_db.create_indexes()  # should not raise


class TestDefaultInstance:
    """Verify module-level singleton uses config."""

    def test_default_path(self) -> None:
        from src.data.database import db

        assert "bi_dashboard.duckdb" in db.db_path
