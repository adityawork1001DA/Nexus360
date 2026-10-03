from sqlalchemy import text
from src.database.connection import get_engine

engine = get_engine()

tables = {
    "customers": "customer_id",
    "subscriptions": "subscription_id",
    "revenue": "transaction_id",
    "cloud_usage": "usage_id",
    "support_tickets": "ticket_id",
}

print()
print("=" * 90)
print("NEXUS360 RAW ID INTEGRITY")
print("=" * 90)

with engine.connect() as connection:

    for table, key in tables.items():

        total = connection.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM raw.{table}"
            )
        ).scalar_one()

        unique = connection.execute(
            text(
                f"SELECT COUNT(DISTINCT {key}) "
                f"FROM raw.{table}"
            )
        ).scalar_one()

        print(
            f"{table:<22}"
            f" total={total:>10,}"
            f" unique={unique:>10,}"
            f" OK={total == unique}"
        )

print("=" * 90)
