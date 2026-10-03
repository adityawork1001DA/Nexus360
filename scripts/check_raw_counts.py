from sqlalchemy import text
from src.database.connection import get_engine

engine = get_engine()

tables = [
    "customers",
    "subscriptions",
    "revenue",
    "cloud_usage",
    "support_tickets",
]

print()
print("=" * 70)
print("NEXUS360 RAW DATABASE COUNTS")
print("=" * 70)

with engine.connect() as connection:
    for table in tables:
        count = connection.execute(
            text(f"SELECT COUNT(*) FROM raw.{table}")
        ).scalar_one()

        print(f"{table:<25} {count:>12,}")

print("=" * 70)
