"""Synthetic business data generator.

Creates realistic dimension and fact data for the BI Dashboard,
including time, product, customer, and sales-transaction tables.
Supports configurable row counts and reproducible seeds.
"""

import random
import uuid
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from src.data.database import Database, db
from src.utils.config import config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

REGIONS = ["North", "South", "East", "West", "Central"]
SEGMENTS = ["Enterprise", "SMB", "Consumer"]
CATEGORIES = ["Electronics", "Clothing", "Food", "Furniture", "Software"]

US_HOLIDAYS = [
    "2022-01-01",
    "2022-01-17",
    "2022-02-21",
    "2022-05-30",
    "2022-07-04",
    "2022-09-05",
    "2022-10-10",
    "2022-11-11",
    "2022-11-24",
    "2022-12-25",
    "2023-01-01",
    "2023-01-16",
    "2023-02-20",
    "2023-05-29",
    "2023-07-04",
    "2023-09-04",
    "2023-10-09",
    "2023-11-10",
    "2023-11-23",
    "2023-12-25",
    "2024-01-01",
    "2024-01-15",
    "2024-02-19",
    "2024-05-27",
    "2024-07-04",
    "2024-09-02",
    "2024-10-14",
    "2024-11-11",
    "2024-11-28",
    "2024-12-25",
]


class DataGenerator:
    """Generate synthetic BI data and insert it into DuckDB.

    Args:
        seed: Random seed for reproducibility.
        database: Optional Database instance (defaults to module-level singleton).
    """

    def __init__(self, seed: int = 42, database: Optional[Database] = None) -> None:
        random.seed(seed)
        np.random.seed(seed)
        self.start_date = date(2022, 1, 1)
        self.end_date = date(2024, 12, 31)
        self._db = database or db

    def generate_time_dimension(self) -> pd.DataFrame:
        """Build a time-dimension DataFrame covering the configured date range.

        Returns:
            DataFrame with columns: date, day_of_week, week, month,
            quarter, year, is_holiday.
        """
        dates = pd.date_range(self.start_date, self.end_date, freq="D")
        holiday_dates = pd.to_datetime(US_HOLIDAYS)
        return pd.DataFrame(
            {
                "date": dates.date,
                "day_of_week": dates.dayofweek,
                "week": dates.isocalendar().week.astype(int),
                "month": dates.month,
                "quarter": dates.quarter,
                "year": dates.year,
                "is_holiday": dates.isin(holiday_dates),
            }
        )

    def generate_products(self, count: int = 50) -> pd.DataFrame:
        """Create a product-dimension DataFrame.

        Args:
            count: Number of products to generate.

        Returns:
            DataFrame with columns: product_id, name, category, cost, price.
        """
        products = []
        for i in range(count):
            category = random.choice(CATEGORIES)
            base_cost = random.uniform(10, 500)
            products.append(
                {
                    "product_id": f"PROD-{i:04d}",
                    "name": f"{category} Item {i}",
                    "category": category,
                    "cost": round(base_cost, 2),
                    "price": round(base_cost * random.uniform(1.2, 2.5), 2),
                }
            )
        return pd.DataFrame(products)

    def generate_customers(self, count: int = 5000) -> pd.DataFrame:
        """Create a customer-dimension DataFrame with realistic signup dates.

        Args:
            count: Number of customers to generate.

        Returns:
            DataFrame with columns: customer_id, name, segment, region,
            signup_date.
        """
        customers = []
        max_days = (self.end_date - self.start_date).days
        for i in range(count):
            offset = int(np.random.exponential(scale=365))
            signup = self.start_date + timedelta(days=min(offset, max_days))
            customers.append(
                {
                    "customer_id": f"CUST-{i:05d}",
                    "name": f"Customer {i}",
                    "segment": random.choices(SEGMENTS, weights=[0.1, 0.3, 0.6])[0],
                    "region": random.choice(REGIONS),
                    "signup_date": signup,
                }
            )
        return pd.DataFrame(customers)

    def generate_transactions(
        self,
        customers: pd.DataFrame,
        products: pd.DataFrame,
        count: int = 100000,
    ) -> pd.DataFrame:
        """Generate sales transactions with seasonality and trends.

        Args:
            customers: Customer dimension DataFrame.
            products: Product dimension DataFrame.
            count: Target number of transactions.

        Returns:
            DataFrame with columns: transaction_id, date, product_id,
            customer_id, region, amount, quantity.
        """
        customer_ids = customers["customer_id"].tolist()
        customer_regions = dict(zip(customers["customer_id"], customers["region"]))
        product_ids = products["product_id"].tolist()
        product_prices = dict(zip(products["product_id"], products["price"]))
        days_range = (self.end_date - self.start_date).days

        transactions = []
        for _ in range(count):
            day_offset = int(np.random.beta(2, 5) * days_range)
            tx_date = self.start_date + timedelta(days=day_offset)

            customer_id = random.choice(customer_ids)
            product_id = random.choice(product_ids)
            quantity = int(np.random.exponential(scale=2)) + 1
            amount = product_prices[product_id] * quantity

            # Q4 seasonality boost
            if tx_date.month in (10, 11, 12):
                amount *= random.uniform(1.0, 1.3)

            transactions.append(
                {
                    "transaction_id": str(uuid.uuid4()),
                    "date": tx_date,
                    "product_id": product_id,
                    "customer_id": customer_id,
                    "region": customer_regions[customer_id],
                    "amount": round(amount, 2),
                    "quantity": quantity,
                }
            )
        return pd.DataFrame(transactions)

    def generate_all(self, transaction_count: Optional[int] = None) -> None:
        """Generate all dimension and fact data and load into DuckDB.

        Args:
            transaction_count: Override the configured transaction count.
        """
        count = transaction_count or config.get("data.transactions_count", 100000)

        logger.info("Generating time dimension...")
        time_df = self.generate_time_dimension()

        logger.info("Generating products...")
        products_df = self.generate_products()

        logger.info("Generating customers...")
        customers_df = self.generate_customers()

        logger.info("Generating %d transactions...", count)
        transactions_df = self.generate_transactions(customers_df, products_df, count)

        with self._db.get_connection() as conn:
            conn.execute("DELETE FROM fact_sales")
            conn.execute("DELETE FROM dim_customer")
            conn.execute("DELETE FROM dim_product")
            conn.execute("DELETE FROM dim_time")

            conn.register("time_df", time_df)
            conn.execute("INSERT INTO dim_time SELECT * FROM time_df")

            conn.register("products_df", products_df)
            conn.execute("INSERT INTO dim_product SELECT * FROM products_df")

            conn.register("customers_df", customers_df)
            conn.execute("INSERT INTO dim_customer SELECT * FROM customers_df")

            conn.register("transactions_df", transactions_df)
            conn.execute("INSERT INTO fact_sales SELECT * FROM transactions_df")

        self._db.create_aggregation_tables()
        logger.info("Data generation complete!")


if __name__ == "__main__":
    db.initialize_schema()
    generator = DataGenerator()
    generator.generate_all()
