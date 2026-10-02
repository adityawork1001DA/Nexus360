from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_engine
from src.ingestion.csv_loader import load_csv_to_raw


LOADS = [
    (
        "data/raw/synthetic/customers.csv",
        "customers",
        "synthetic_crm",
    ),
    (
        "data/raw/synthetic/subscriptions.csv",
        "subscriptions",
        "synthetic_billing",
    ),
    (
        "data/raw/synthetic/revenue.csv",
        "revenue",
        "synthetic_billing",
    ),
    (
        "data/raw/synthetic/cloud_usage.csv",
        "cloud_usage",
        "synthetic_telemetry",
    ),
    (
        "data/raw/synthetic/support_tickets.csv",
        "support_tickets",
        "synthetic_support",
    ),
]


def clear_synthetic_raw() -> None:
    """
    Clear synthetic RAW tables before a full development reload.

    Child/source-detail tables are listed first for clarity.
    """

    engine = get_engine()

    query = text(
        """
        TRUNCATE TABLE
            raw.support_tickets,
            raw.cloud_usage,
            raw.revenue,
            raw.subscriptions,
            raw.customers;
        """
    )

    with engine.begin() as connection:
        connection.execute(query)

    print(
        "[OK] Previous synthetic RAW data cleared."
    )


def main() -> None:

    print()
    print("=" * 70)
    print(
        "NEXUS 360 - SYNTHETIC RAW INGESTION"
    )
    print("=" * 70)

    print(
        "Clearing previous synthetic raw data..."
    )

    clear_synthetic_raw()

    print()

    successful_loads = 0

    for (
        filepath,
        table_name,
        source_system,
    ) in LOADS:

        load_csv_to_raw(
            filepath=filepath,
            table_name=table_name,
            source_system=source_system,
        )

        successful_loads += 1

    print()
    print("=" * 70)
    print(
        f"RAW ingestion completed successfully. "
        f"{successful_loads}/{len(LOADS)} datasets loaded."
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()