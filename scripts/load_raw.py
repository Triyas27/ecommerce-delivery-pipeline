import duckdb
from pathlib import Path

RAW_DIR = Path("data/raw")
DB_PATH = Path("data/olist.duckdb")


def table_name_for(csv_path: Path) -> str:
    stem = csv_path.stem  # "olist_orders_dataset"
    stem = stem.replace("olist_", "").replace("_dataset", "")
    return f"raw_{stem}"


def main():
    con = duckdb.connect(str(DB_PATH))

    for csv_path in sorted(RAW_DIR.glob("*.csv")):
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
