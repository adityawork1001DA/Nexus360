import sys

import pandas as pd

from src.quality.checks import (
    count_duplicates,
    count_negative_values,
    count_nulls,
)


FAILURES = []


def fail(
    dataset: str,
    rule: str,
    count: int,
) -> None:

    if count > 0:

        FAILURES.append(
            (
                dataset,
                rule,
                count,
            )
        )

        print(
            f"[FAIL] {dataset:<20} "
            f"{rule:<35} "
            f"{count:,}"
        )

    else:

        print(
            f"[PASS] {dataset:<20} "
            f"{rule}"
        )


def main() -> None:

    customers = pd.read_csv(
        "data/raw/synthetic/customers.csv"
    )

    subscriptions = pd.read_csv(
        "data/raw/synthetic/subscriptions.csv"
    )

    revenue = pd.read_csv(
        "data/raw/synthetic/revenue.csv"
    )

    usage = pd.read_csv(
        "data/raw/synthetic/cloud_usage.csv"
    )

    tickets = pd.read_csv(
        "data/raw/synthetic/support_tickets.csv"
    )

    fail(
        "customers",
        "duplicate customer_id",
        count_duplicates(
            customers,
            ["customer_id"],
        ),
    )

    fail(
        "customers",
        "required nulls",
        count_nulls(
            customers,
            [
                "customer_id",
                "customer_segment",
                "region_code",
            ],
        ),
    )

    fail(
        "subscriptions",
        "duplicate subscription_id",
        count_duplicates(
            subscriptions,
            ["subscription_id"],
        ),
    )

    fail(
        "subscriptions",
        "negative contract value",
        count_negative_values(
            subscriptions,
            "contract_value_usd",
        ),
    )

    fail(
        "revenue",
        "duplicate transaction_id",
        count_duplicates(
            revenue,
            ["transaction_id"],
        ),
    )

    fail(
        "revenue",
        "negative net revenue",
        count_negative_values(
            revenue,
            "net_revenue_usd",
        ),
    )

    fail(
        "usage",
        "duplicate usage_id",
        count_duplicates(
            usage,
            ["usage_id"],
        ),
    )

    fail(
        "usage",
        "negative compute",
        count_negative_values(
            usage,
            "compute_hours",
        ),
    )

    fail(
        "tickets",
        "duplicate ticket_id",
        count_duplicates(
            tickets,
            ["ticket_id"],
        ),
    )

    print()

    if FAILURES:

        print(
            f"{len(FAILURES)} "
            "quality rule(s) failed."
        )

        sys.exit(1)

    print(
        "All synthetic data "
        "quality checks passed."
    )


if __name__ == "__main__":
    main()