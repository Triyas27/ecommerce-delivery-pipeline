import argparse
from pathlib import Path

import duckdb

DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_DB_PATH = Path("data/olist.duckdb")


def table_name_for(csv_path: Path) -> str:
    stem = csv_path.stem  # "olist_orders_dataset"
    stem = stem.replace("olist_", "").replace("_dataset", "")
    return f"raw_{stem}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    con = duckdb.connect(str(args.db_path))

    for csv_path in sorted(args.raw_dir.glob("*.csv")):
        table = table_name_for(csv_path)
        con.execute(f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT * FROM read_csv_auto('{csv_path.as_posix()}')
        """)
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"loaded {table}: {count} rows")

    con.close()


if __name__ == "__main__":
    main()
