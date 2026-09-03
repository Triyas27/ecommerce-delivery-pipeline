"""One-off utility: sample a small, referentially-consistent slice of the
real Olist data for CI to use, since the full dataset can't live in the repo.
Run manually and commit the output - this is not part of the regular pipeline.
"""

import duckdb
from pathlib import Path

DB_PATH = "data/olist.duckdb"
FIXTURE_DIR = Path("tests/fixtures/raw")
SAMPLE_SIZE = 150
SEED = 42


def main():
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB_PATH)

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE sampled_orders AS
        SELECT * FROM raw_orders
        USING SAMPLE {SAMPLE_SIZE} ROWS (reservoir, {SEED})
    """)

    tables = {
        "olist_orders_dataset": "SELECT * FROM sampled_orders",
        "olist_customers_dataset": """
            SELECT * FROM raw_customers
            WHERE customer_id IN (SELECT customer_id FROM sampled_orders)
        """,
        "olist_order_items_dataset": """
            SELECT * FROM raw_order_items
            WHERE order_id IN (SELECT order_id FROM sampled_orders)
        """,
        "olist_order_payments_dataset": """
            SELECT * FROM raw_order_payments
            WHERE order_id IN (SELECT order_id FROM sampled_orders)
        """,
        "olist_order_reviews_dataset": """
            SELECT * FROM raw_order_reviews
            WHERE order_id IN (SELECT order_id FROM sampled_orders)
        """,
        "olist_products_dataset": """
            SELECT * FROM raw_products
            WHERE product_id IN (
                SELECT DISTINCT product_id FROM raw_order_items
                WHERE order_id IN (SELECT order_id FROM sampled_orders)
            )
        """,
        "olist_sellers_dataset": """
            SELECT * FROM raw_sellers
            WHERE seller_id IN (
                SELECT DISTINCT seller_id FROM raw_order_items
                WHERE order_id IN (SELECT order_id FROM sampled_orders)
            )
        """,
        "olist_geolocation_dataset": """
            SELECT * FROM raw_geolocation
            WHERE geolocation_zip_code_prefix IN (
                SELECT customer_zip_code_prefix FROM raw_customers
                WHERE customer_id IN (SELECT customer_id FROM sampled_orders)
                UNION
                SELECT seller_zip_code_prefix FROM raw_sellers
                WHERE seller_id IN (
                    SELECT DISTINCT seller_id FROM raw_order_items
                    WHERE order_id IN (SELECT order_id FROM sampled_orders)
                )
            )
            QUALIFY row_number() OVER (
                PARTITION BY geolocation_zip_code_prefix
                ORDER BY geolocation_lat
            ) <= 3
        """,
        "product_category_name_translation": "SELECT * FROM raw_product_category_name_translation",
    }

    for filename, query in tables.items():
        df = con.execute(query).fetchdf()
        out_path = FIXTURE_DIR / f"{filename}.csv"
        df.to_csv(out_path, index=False)
        print(f"wrote {out_path}: {len(df)} rows")

    con.close()


if __name__ == "__main__":
    main()
