from pathlib import Path
from sqlalchemy import text

from src.database.connection import get_engine

root = Path.cwd()

files = [
    root / "sql" / "dml" / "002_raw_to_staging.sql",
    root / "sql" / "dml" / "003_load_customer_dimension.sql",
]

engine = get_engine()

for filepath in files:

    print(f"[RUN] {filepath.name}")

    sql = filepath.read_text(
        encoding="utf-8"
    )

    with engine.begin() as conn:
        conn.execute(text(sql))

    print(f"[OK]  {filepath.name}")

with engine.connect() as conn:

    for label, query in [
        (
            "RAW",
            "SELECT COUNT(*) FROM raw.customers",
        ),
        (
            "STAGING",
            "SELECT COUNT(*) FROM staging.customers",
        ),
        (
            "WAREHOUSE",
            "SELECT COUNT(*) FROM warehouse.dim_customer",
        ),
    ]:

        count = conn.execute(
            text(query)
        ).scalar_one()

        print(
            f"{label:<15} {int(count):,}"
        )
