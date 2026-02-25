"""DuckDB database management module.

Handles connection lifecycle, schema creation, and pre-computed
aggregation tables for the BI Dashboard.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

import duckdb

from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Database:
    """Manages a DuckDB database, including schema and aggregation tables.

    Attributes:
        db_path: Filesystem path for the DuckDB file.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path: str = db_path or config.get(
            "data.database_path", "data/bi_dashboard.duckdb"
        )
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Yield a DuckDB connection and close it on exit.

        Yields:
            An open ``DuckDBPyConnection``.
        """
        conn = duckdb.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Create all dimension and fact tables if they do not exist."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dim_time (
                    date DATE PRIMARY KEY,
                    day_of_week INTEGER,
                    week INTEGER,
                    month INTEGER,
                    quarter INTEGER,
                    year INTEGER,
                    is_holiday BOOLEAN
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS dim_product (
                    product_id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    cost DECIMAL(10,2) NOT NULL,
                    price DECIMAL(10,2) NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS dim_customer (
                    customer_id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    segment VARCHAR NOT NULL,
                    region VARCHAR NOT NULL,
                    signup_date DATE NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS fact_sales (
                    transaction_id VARCHAR PRIMARY KEY,
                    date DATE NOT NULL,
                    product_id VARCHAR NOT NULL,
                    customer_id VARCHAR NOT NULL,
                    region VARCHAR NOT NULL,
                    amount DECIMAL(12,2) NOT NULL,
                    quantity INTEGER NOT NULL
                )
            """)

        logger.info("Database schema initialized successfully")

    def create_aggregation_tables(self) -> None:
        """Build pre-computed aggregation tables for dashboard speed."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE OR REPLACE TABLE agg_daily_region AS
                SELECT
                    date,
                    region,
                    SUM(amount) AS revenue,
                    COUNT(*) AS transaction_count,
                    COUNT(DISTINCT customer_id) AS unique_customers
                FROM fact_sales
                GROUP BY date, region
            """)

            conn.execute("""
                CREATE OR REPLACE TABLE agg_daily_category AS
                SELECT
                    s.date,
                    p.category,
                    SUM(s.amount) AS revenue,
                    SUM(s.quantity) AS units_sold
                FROM fact_sales s
                JOIN dim_product p ON s.product_id = p.product_id
                GROUP BY s.date, p.category
            """)

            conn.execute("""
                CREATE OR REPLACE TABLE agg_cohort AS
                SELECT
                    DATE_TRUNC('month', c.signup_date) AS cohort_month,
                    DATE_TRUNC('month', s.date) AS activity_month,
                    COUNT(DISTINCT s.customer_id) AS active_customers,
                    SUM(s.amount) AS revenue
                FROM fact_sales s
                JOIN dim_customer c ON s.customer_id = c.customer_id
                GROUP BY
                    DATE_TRUNC('month', c.signup_date),
                    DATE_TRUNC('month', s.date)
            """)

        logger.info("Aggregation tables created successfully")

    def create_indexes(self) -> None:
        """Create indexes for common query patterns."""
        with self.get_connection() as conn:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sales_date ON fact_sales(date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sales_region ON fact_sales(region)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sales_product ON fact_sales(product_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sales_customer "
                "ON fact_sales(customer_id)"
            )

        logger.info("Indexes created successfully")


db = Database()
