from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

import scripts.generate_enterprise_data as base
from src.database.connection import get_engine


OUTPUT_DIR = Path("data/raw/synthetic_incremental")

DATASETS = {
    "customers.csv": "customers",
    "subscriptions.csv": "subscriptions",
    "revenue.csv": "revenue",
    "cloud_usage.csv": "usage",
    "support_tickets.csv": "tickets",
}

ID_CONFIG = {
    "customers": (
        "raw.customers",
        "customer_id",
        "CUST-",
        6,
    ),
    "subscriptions": (
        "raw.subscriptions",
        "subscription_id",
        "SUB-",
        8,
    ),
    "revenue": (
        "raw.revenue",
        "transaction_id",
        "TXN-",
        10,
    ),
    "usage": (
        "raw.cloud_usage",
        "usage_id",
        "USE-",
        10,
    ),
    "tickets": (
        "raw.support_tickets",
        "ticket_id",
        "TKT-",
        9,
    ),
}


def get_max_numeric_id(
    table: str,
    column: str,
) -> int:
    """
    Read the highest numeric suffix currently present
    in PostgreSQL.

    Example:
        CUST-002500 -> 2500
    """

    engine = get_engine()

    query = text(
        f"""
        SELECT COALESCE(
            MAX(
                NULLIF(
                    regexp_replace(
                        {column},
                        '\\D',
                        '',
                        'g'
                    ),
                    ''
                )::BIGINT
            ),
            0
        )
        FROM {table}
        """
    )

    with engine.connect() as connection:
        value = connection.execute(
            query
        ).scalar_one()

    return int(value or 0)


def current_id_state() -> dict[str, int]:
    state: dict[str, int] = {}

    for key, (
        table,
        column,
        _prefix,
        _width,
    ) in ID_CONFIG.items():

        state[key] = get_max_numeric_id(
            table,
            column,
        )

    return state


def shift_ids(
    dataframe: pd.DataFrame,
    column: str,
    *,
    start_after: int,
    prefix: str,
    width: int,
) -> pd.DataFrame:
    """
    Replace generated IDs with IDs continuing from
    PostgreSQL's current maximum.
    """

    result = dataframe.copy()

    result[column] = [
        f"{prefix}{number:0{width}d}"
        for number in range(
            start_after + 1,
            start_after + 1 + len(result),
        )
    ]

    return result


def remap_foreign_key(
    dataframe: pd.DataFrame,
    column: str,
    mapping: dict[str, str],
) -> pd.DataFrame:

    result = dataframe.copy()

    result[column] = (
        result[column]
        .astype(str)
        .map(mapping)
    )

    if result[column].isna().any():
        raise RuntimeError(
            f"Unable to remap all values for {column}."
        )

    return result


def expected_columns() -> dict[str, list[str]]:
    """
    Business columns expected by RAW PostgreSQL tables.

    Audit metadata columns are intentionally excluded because
    the ingestion layer owns those fields.
    """

    return {
        "customers.csv": [
            "customer_id",
            "customer_name",
            "industry",
            "customer_segment",
            "country_code",
            "region_code",
            "employee_band",
            "annual_revenue_band",
            "acquisition_channel",
            "signup_date",
            "customer_status",
            "is_ai_customer",
        ],
        "subscriptions.csv": [
            "subscription_id",
            "customer_id",
            "product_code",
            "start_date",
            "end_date",
            "billing_frequency",
            "contract_value_usd",
            "seats",
            "subscription_status",
            "auto_renew",
        ],
        "revenue.csv": [
            "transaction_id",
            "transaction_date",
            "customer_id",
            "product_code",
            "region_code",
            "currency_code",
            "quantity",
            "gross_revenue_local",
            "discount_local",
            "net_revenue_local",
            "fx_rate_to_usd",
            "net_revenue_usd",
            "estimated_cost_usd",
            "gross_profit_usd",
            "revenue_type",
        ],
        "cloud_usage.csv": [
            "usage_id",
            "usage_date",
            "customer_id",
            "product_code",
            "region_code",
            "datacenter_code",
            "compute_hours",
            "storage_gb",
            "network_gb",
            "ai_tokens_million",
            "requests_count",
            "failed_requests",
            "estimated_cost_usd",
            "carbon_estimate_kg",
        ],
        "support_tickets.csv": [
            "ticket_id",
            "customer_id",
            "product_code",
            "opened_date",
            "closed_date",
            "severity",
            "category",
            "resolution_hours",
            "sla_target_hours",
            "sla_met",
            "reopened",
            "customer_satisfaction",
        ],
    }


def validate_dataset(
    filename: str,
    dataframe: pd.DataFrame,
) -> None:

    expected = expected_columns()[filename]
    actual = list(dataframe.columns)

    if actual != expected:
        missing = [
            col
            for col in expected
            if col not in actual
        ]

        extra = [
            col
            for col in actual
            if col not in expected
        ]

        raise RuntimeError(
            f"{filename} schema mismatch.\n"
            f"Missing: {missing}\n"
            f"Extra: {extra}\n"
            f"Expected: {expected}\n"
            f"Actual: {actual}"
        )

    if dataframe.empty:
        raise RuntimeError(
            f"{filename} contains no rows."
        )


def validate_unique_ids(
    dataframe: pd.DataFrame,
    column: str,
) -> None:

    if dataframe[column].duplicated().any():
        raise RuntimeError(
            f"Duplicate IDs detected in {column}."
        )


def save_dataset(
    dataframe: pd.DataFrame,
    filename: str,
) -> None:

    validate_dataset(
        filename,
        dataframe,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = OUTPUT_DIR / filename

    dataframe.to_csv(
        path,
        index=False,
    )

    print(
        f"{filename:<30}"
        f"{len(dataframe):>12,} rows"
    )


def generate_incremental(
    customer_count: int,
) -> None:

    if customer_count <= 0:
        raise ValueError(
            "--customers must be greater than zero."
        )

    print()
    print("=" * 70)
    print(
        "NEXUS 360 - SAFE INCREMENTAL ENTERPRISE GENERATOR"
    )
    print("=" * 70)

    state = current_id_state()

    print()
    print("Current PostgreSQL ID state:")
    print(
        f"Customer:      {state['customers']:,}"
    )
    print(
        f"Subscription:  {state['subscriptions']:,}"
    )
    print(
        f"Transaction:   {state['revenue']:,}"
    )
    print(
        f"Usage:         {state['usage']:,}"
    )
    print(
        f"Ticket:        {state['tickets']:,}"
    )

    # --------------------------------------------------------
    # GENERATE USING ORIGINAL PRODUCTION LOGIC
    # --------------------------------------------------------

    original_count = base.CUSTOMER_COUNT

    try:
        base.CUSTOMER_COUNT = customer_count

        customers = base.generate_customers()

        subscriptions = (
            base.generate_subscriptions(
                customers
            )
        )

        revenue = base.generate_revenue(
            customers,
            subscriptions,
        )

        usage = base.generate_usage(
            customers,
            subscriptions,
        )

        tickets = (
            base.generate_support_tickets(
                customers,
                usage,
            )
        )

    finally:
        base.CUSTOMER_COUNT = original_count

    # --------------------------------------------------------
    # CUSTOMER IDS
    # --------------------------------------------------------

    old_customer_ids = (
        customers["customer_id"]
        .astype(str)
        .tolist()
    )

    customers = shift_ids(
        customers,
        "customer_id",
        start_after=state["customers"],
        prefix="CUST-",
        width=6,
    )

    new_customer_ids = (
        customers["customer_id"]
        .astype(str)
        .tolist()
    )

    customer_mapping = dict(
        zip(
            old_customer_ids,
            new_customer_ids,
        )
    )

    # --------------------------------------------------------
    # FOREIGN KEYS
    # --------------------------------------------------------

    subscriptions = remap_foreign_key(
        subscriptions,
        "customer_id",
        customer_mapping,
    )

    revenue = remap_foreign_key(
        revenue,
        "customer_id",
        customer_mapping,
    )

    usage = remap_foreign_key(
        usage,
        "customer_id",
        customer_mapping,
    )

    tickets = remap_foreign_key(
        tickets,
        "customer_id",
        customer_mapping,
    )

    # --------------------------------------------------------
    # ENTITY IDS
    # --------------------------------------------------------

    subscriptions = shift_ids(
        subscriptions,
        "subscription_id",
        start_after=state["subscriptions"],
        prefix="SUB-",
        width=8,
    )

    revenue = shift_ids(
        revenue,
        "transaction_id",
        start_after=state["revenue"],
        prefix="TXN-",
        width=10,
    )

    usage = shift_ids(
        usage,
        "usage_id",
        start_after=state["usage"],
        prefix="USE-",
        width=10,
    )

    tickets = shift_ids(
        tickets,
        "ticket_id",
        start_after=state["tickets"],
        prefix="TKT-",
        width=9,
    )

    # --------------------------------------------------------
    # CUSTOMER EXPORT
    # Original generator uses these only internally.
    # --------------------------------------------------------

    customers_export = customers.drop(
        columns=[
            "currency_code",
            "country_name",
        ],
    )

    # --------------------------------------------------------
    # VALIDATE IDS
    # --------------------------------------------------------

    validate_unique_ids(
        customers_export,
        "customer_id",
    )

    validate_unique_ids(
        subscriptions,
        "subscription_id",
    )

    validate_unique_ids(
        revenue,
        "transaction_id",
    )

    validate_unique_ids(
        usage,
        "usage_id",
    )

    validate_unique_ids(
        tickets,
        "ticket_id",
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    print()
    print("Writing validated incremental batch...")
    print()

    save_dataset(
        customers_export,
        "customers.csv",
    )

    save_dataset(
        subscriptions,
        "subscriptions.csv",
    )

    save_dataset(
        revenue,
        "revenue.csv",
    )

    save_dataset(
        usage,
        "cloud_usage.csv",
    )

    save_dataset(
        tickets,
        "support_tickets.csv",
    )

    print()
    print("=" * 70)
    print(
        "Incremental generation completed successfully."
    )
    print(
        "No existing PostgreSQL rows were modified."
    )
    print("=" * 70)
    print()


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Generate a schema-compatible incremental "
            "Nexus360 enterprise dataset."
        )
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=10,
        help=(
            "Number of new customers to generate."
        ),
    )

    return parser.parse_args()


def main() -> None:

    args = parse_args()

    generate_incremental(
        customer_count=args.customers,
    )


if __name__ == "__main__":
    main()