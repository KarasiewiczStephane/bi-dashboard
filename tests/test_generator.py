"""Tests for the synthetic data generator."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.database import Database
from src.data.generator import DataGenerator


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Database:
    """Create a temporary DuckDB database with schema."""
    db_path = str(tmp_path / "test_gen.duckdb")
    database = Database(db_path=db_path)
    database.initialize_schema()
    return database


@pytest.fixture()
def generator(tmp_db: Database) -> DataGenerator:
    """Return a DataGenerator wired to the temp database."""
    return DataGenerator(seed=42, database=tmp_db)


class TestTimeDimension:
    """Verify time dimension generation."""

    def test_date_range(self, generator: DataGenerator) -> None:
        df = generator.generate_time_dimension()
        assert df["date"].min().year == 2022
        assert df["date"].max().year == 2024

    def test_columns(self, generator: DataGenerator) -> None:
        df = generator.generate_time_dimension()
        expected = {
            "date",
            "day_of_week",
            "week",
            "month",
            "quarter",
            "year",
            "is_holiday",
        }
        assert set(df.columns) == expected

    def test_holidays_flagged(self, generator: DataGenerator) -> None:
        df = generator.generate_time_dimension()
        assert df["is_holiday"].any()


class TestProducts:
    """Verify product generation."""

    def test_count(self, generator: DataGenerator) -> None:
        df = generator.generate_products(count=20)
        assert len(df) == 20

    def test_price_above_cost(self, generator: DataGenerator) -> None:
        df = generator.generate_products()
        assert (df["price"] >= df["cost"]).all()

    def test_categories(self, generator: DataGenerator) -> None:
        df = generator.generate_products()
        assert set(df["category"].unique()).issubset(
            {"Electronics", "Clothing", "Food", "Furniture", "Software"}
        )


class TestCustomers:
    """Verify customer generation."""

    def test_count(self, generator: DataGenerator) -> None:
        df = generator.generate_customers(count=100)
        assert len(df) == 100

    def test_regions(self, generator: DataGenerator) -> None:
        df = generator.generate_customers()
        assert set(df["region"].unique()).issubset(
            {"North", "South", "East", "West", "Central"}
        )

    def test_segments(self, generator: DataGenerator) -> None:
        df = generator.generate_customers()
        assert set(df["segment"].unique()).issubset({"Enterprise", "SMB", "Consumer"})


class TestTransactions:
    """Verify sales transaction generation."""

    def test_count(self, generator: DataGenerator) -> None:
        customers = generator.generate_customers(count=50)
        products = generator.generate_products(count=10)
        df = generator.generate_transactions(customers, products, count=200)
        assert len(df) == 200

    def test_valid_foreign_keys(self, generator: DataGenerator) -> None:
        customers = generator.generate_customers(count=50)
        products = generator.generate_products(count=10)
        df = generator.generate_transactions(customers, products, count=100)
        assert set(df["customer_id"].unique()).issubset(set(customers["customer_id"]))
        assert set(df["product_id"].unique()).issubset(set(products["product_id"]))

    def test_positive_amounts(self, generator: DataGenerator) -> None:
        customers = generator.generate_customers(count=50)
        products = generator.generate_products(count=10)
        df = generator.generate_transactions(customers, products, count=100)
        assert (df["amount"] > 0).all()


class TestGenerateAll:
    """End-to-end data generation into DuckDB."""

    def test_generates_and_inserts(
        self, generator: DataGenerator, tmp_db: Database
    ) -> None:
        generator.generate_all(transaction_count=500)
        with tmp_db.get_connection() as conn:
            time_count = conn.execute("SELECT COUNT(*) FROM dim_time").fetchone()[0]
            prod_count = conn.execute("SELECT COUNT(*) FROM dim_product").fetchone()[0]
            cust_count = conn.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0]
            sales_count = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]

        assert time_count > 0
        assert prod_count == 50
        assert cust_count == 5000
        assert sales_count == 500

    def test_aggregation_tables_populated(
        self, generator: DataGenerator, tmp_db: Database
    ) -> None:
        generator.generate_all(transaction_count=500)
        with tmp_db.get_connection() as conn:
            agg_count = conn.execute(
                "SELECT COUNT(*) FROM agg_daily_region"
            ).fetchone()[0]
        assert agg_count > 0

    def test_reproducibility(self, tmp_db: Database) -> None:
        gen1 = DataGenerator(seed=99, database=tmp_db)
        products1 = gen1.generate_products()
        gen2 = DataGenerator(seed=99, database=tmp_db)
        products2 = gen2.generate_products()
        pd.testing.assert_frame_equal(products1, products2)
