from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

from src.ingestion.reference_data import (
    COUNTRIES,
    DATACENTERS_BY_REGION,
)


SEED = 42

random.seed(SEED)
np.random.seed(SEED)

fake = Faker()
Faker.seed(SEED)


OUTPUT_DIR = Path(
    "data/raw/synthetic"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


CUSTOMER_COUNT = 2500

START_DATE = date(
    2023,
    1,
    1,
)

END_DATE = date(
    2026,
    9,
    30,
)


PRODUCTS = [
    "NC-COMPUTE",
    "NC-STORAGE",
    "NC-SQL",
    "NC-WAREHOUSE",
    "NC-AIMODEL",
    "NC-AISEARCH",
    "NC-SECURITY",
    "NC-ANALYTICS",
    "NC-CONTAINER",
    "NC-INTEGRATION",
]


AI_PRODUCTS = {
    "NC-AIMODEL",
    "NC-AISEARCH",
}


INDUSTRIES = [
    "Banking",
    "Insurance",
    "Retail",
    "Healthcare",
    "Manufacturing",
    "Telecommunications",
    "Technology",
    "Education",
    "Energy",
    "Media",
    "Transportation",
    "Professional Services",
]


SEGMENTS = [
    "SMB",
    "Mid-Market",
    "Enterprise",
    "Strategic",
]


SEGMENT_PROBABILITY = [
    0.42,
    0.31,
    0.20,
    0.07,
]


SEGMENT_BASE_VALUE = {
    "SMB": 12_000,
    "Mid-Market": 55_000,
    "Enterprise": 220_000,
    "Strategic": 850_000,
}


SEGMENT_PRODUCT_COUNT = {
    "SMB": (1, 3),
    "Mid-Market": (2, 5),
    "Enterprise": (3, 7),
    "Strategic": (5, 9),
}


CURRENCY_TO_USD = {
    "USD": 1.00,
    "CAD": 0.74,
    "BRL": 0.18,
    "GBP": 1.28,
    "EUR": 1.09,
    "AED": 0.2723,
    "INR": 0.012,
    "SGD": 0.74,
    "JPY": 0.0067,
    "AUD": 0.66,
}


def random_date(
    start: date,
    end: date,
) -> date:

    delta = (
        end - start
    ).days

    return (
        start
        + timedelta(
            days=random.randint(
                0,
                delta,
            )
        )
    )


def generate_customers() -> pd.DataFrame:

    rows = []

    for number in range(
        1,
        CUSTOMER_COUNT + 1,
    ):

        segment = random.choices(
            SEGMENTS,
            weights=SEGMENT_PROBABILITY,
            k=1,
        )[0]

        (
            country_code,
            country_name,
            region_code,
            currency_code,
        ) = random.choice(
            COUNTRIES
        )

        ai_probability = {
            "SMB": 0.15,
            "Mid-Market": 0.28,
            "Enterprise": 0.48,
            "Strategic": 0.67,
        }[segment]

        is_ai_customer = (
            random.random()
            < ai_probability
        )

        signup_date = random_date(
            date(2021, 1, 1),
            date(2025, 12, 31),
        )

        rows.append(
            {
                "customer_id":
                    f"CUST-{number:06d}",

                "customer_name":
                    fake.company(),

                "industry":
                    random.choice(
                        INDUSTRIES
                    ),

                "customer_segment":
                    segment,

                "country_code":
                    country_code,

                "region_code":
                    region_code,

                "employee_band":
                    random.choice(
                        [
                            "1-49",
                            "50-249",
                            "250-999",
                            "1000-4999",
                            "5000+",
                        ]
                    ),

                "annual_revenue_band":
                    random.choice(
                        [
                            "<$10M",
                            "$10M-$50M",
                            "$50M-$250M",
                            "$250M-$1B",
                            "$1B+",
                        ]
                    ),

                "acquisition_channel":
                    random.choice(
                        [
                            "Direct Sales",
                            "Partner",
                            "Digital",
                            "Marketplace",
                            "Enterprise Agreement",
                        ]
                    ),

                "signup_date":
                    signup_date,

                "customer_status":
                    "Active",

                "is_ai_customer":
                    is_ai_customer,

                "currency_code":
                    currency_code,

                "country_name":
                    country_name,
            }
        )

    return pd.DataFrame(rows)


def generate_subscriptions(
    customers: pd.DataFrame,
) -> pd.DataFrame:

    rows = []

    subscription_number = 1

    for customer in customers.itertuples():

        segment = str(customer.customer_segment)

        low, high = (
            SEGMENT_PRODUCT_COUNT[
                segment
            ]
        )

        product_count = random.randint(
            low,
            high,
        )

        available_products = PRODUCTS.copy()

        if not customer.is_ai_customer:

            available_products = [
                p
                for p in available_products
                if p not in AI_PRODUCTS
            ]

        selected_products = random.sample(
            available_products,
            k=min(
                product_count,
                len(available_products),
            ),
        )

        for product in selected_products:

            signup_date_value = customer.signup_date

            if isinstance(
                signup_date_value,
                bytes,
            ):
                signup_date_value = (
                    signup_date_value.decode(
                        "utf-8"
                    )
                )

            customer_signup_date = (
                pd.to_datetime(
                    str(signup_date_value)
                ).date()
            )

            start = max(
                customer_signup_date,
                random_date(
                    START_DATE,
                    date(
                        2025,
                        12,
                        31,
                    ),
                ),
            )

            customer_segment = customer.customer_segment

            if isinstance(
                customer_segment,
                bytes,
            ):
                customer_segment = (
                    customer_segment.decode(
                        "utf-8"
                    )
                )

            customer_segment = str(
                customer_segment
            ).strip()

            contract_value = (
                SEGMENT_BASE_VALUE[
                    customer_segment
                ]
                * random.uniform(
                    0.55,
                    1.75,
                )
            )

            if product in AI_PRODUCTS:
                contract_value *= (
                    random.uniform(
                        1.1,
                        1.6,
                    )
                )

            billing_frequency = (
                random.choices(
                    [
                        "Monthly",
                        "Quarterly",
                        "Annual",
                    ],
                    weights=[
                        0.35,
                        0.20,
                        0.45,
                    ],
                    k=1,
                )[0]
            )

            end = start + timedelta(
                days=random.choice(
                    [
                        365,
                        730,
                        1095,
                    ]
                )
            )

            status = (
                "Active"
                if end >= END_DATE
                else "Expired"
            )

            rows.append(
                {
                    "subscription_id":
                        (
                            "SUB-"
                            f"{subscription_number:08d}"
                        ),

                    "customer_id":
                        customer.customer_id,

                    "product_code":
                        product,

                    "start_date":
                        start,

                    "end_date":
                        end,

                    "billing_frequency":
                        billing_frequency,

                    "contract_value_usd":
                        round(
                            contract_value,
                            2,
                        ),

                    "seats":
                        random.randint(
                            5,
                            {
                                "SMB": 100,
                                "Mid-Market": 500,
                                "Enterprise": 3000,
                                "Strategic": 15000,
                            }[
                                str(
                                    customer.customer_segment
                                ).strip()
                            ],
                        ),

                    "subscription_status":
                        status,

                    "auto_renew":
                        random.random()
                        < 0.82,
                }
            )

            subscription_number += 1

    return pd.DataFrame(rows)

def generate_revenue(
    customers: pd.DataFrame,
    subscriptions: pd.DataFrame,
) -> pd.DataFrame:

    customer_lookup = (
        customers
        .set_index("customer_id")
        .to_dict("index")
    )

    rows = []

    transaction_number = 1

    for subscription in subscriptions.itertuples():

        customer = customer_lookup[
            subscription.customer_id
        ]

        start_date = subscription.start_date
        if isinstance(start_date, bytes):
            start_date = start_date.decode("utf-8")
        if not isinstance(start_date, date):
            start_date = pd.to_datetime(str(start_date)).date()

        end_date = subscription.end_date
        if isinstance(end_date, bytes):
            end_date = end_date.decode("utf-8")
        if not isinstance(end_date, date):
            end_date = pd.to_datetime(str(end_date)).date()

        current = max(
            start_date,
            START_DATE,
        )

        final_date = min(
            end_date,
            END_DATE,
        )

        contract_value = (
            float(
                str(
                    subscription.contract_value_usd
                ).replace(",", "").strip()
            )
            if subscription.contract_value_usd is not None
            and str(
                subscription.contract_value_usd
            ).strip() != ""
            else 0.0
        )

        monthly_usd = (
            contract_value
            / 12
        )

        while current <= final_date:

            growth_factor = (
                1
                + (
                    (
                        current.year
                        - START_DATE.year
                    )
                    * 0.035
                )
            )

            noise = random.uniform(
                0.88,
                1.14,
            )

            revenue_usd = (
                monthly_usd
                * growth_factor
                * noise
            )

            currency = customer[
                "currency_code"
            ]

            fx_to_usd = (
                CURRENCY_TO_USD[
                    currency
                ]
            )

            local_gross = (
                revenue_usd
                / fx_to_usd
            )

            discount_pct = (
                random.uniform(
                    0.01,
                    0.08,
                )
            )

            local_discount = (
                local_gross
                * discount_pct
            )

            local_net = (
                local_gross
                - local_discount
            )

            net_usd = (
                local_net
                * fx_to_usd
            )

            margin_pct = (
                random.uniform(
                    0.48,
                    0.78,
                )
            )

            cost_usd = (
                net_usd
                * (
                    1
                    - margin_pct
                )
            )

            gross_profit = (
                net_usd
                - cost_usd
            )

            rows.append(
                {
                    "transaction_id":
                        (
                            "TXN-"
                            f"{transaction_number:010d}"
                        ),

                    "transaction_date":
                        current,

                    "customer_id":
                        subscription.customer_id,

                    "product_code":
                        subscription.product_code,

                    "region_code":
                        customer["region_code"],

                    "currency_code":
                        currency,

                    "quantity":
                        round(
                            random.uniform(
                                1,
                                100,
                            ),
                            4,
                        ),

                    "gross_revenue_local":
                        round(
                            local_gross,
                            2,
                        ),

                    "discount_local":
                        round(
                            local_discount,
                            2,
                        ),

                    "net_revenue_local":
                        round(
                            local_net,
                            2,
                        ),

                    "fx_rate_to_usd":
                        fx_to_usd,

                    "net_revenue_usd":
                        round(
                            net_usd,
                            2,
                        ),

                    "estimated_cost_usd":
                        round(
                            cost_usd,
                            2,
                        ),

                    "gross_profit_usd":
                        round(
                            gross_profit,
                            2,
                        ),

                    "revenue_type":
                        (
                            "AI Consumption"
                            if (
                                subscription.product_code
                                in AI_PRODUCTS
                            )
                            else "Cloud Consumption"
                        ),
                }
            )

            transaction_number += 1

            current = (
                current
                + pd.DateOffset(
                    months=1
                )
            ).date()

    return pd.DataFrame(rows)

def generate_usage(
    customers: pd.DataFrame,
    subscriptions: pd.DataFrame,
) -> pd.DataFrame:

    customer_lookup = (
        customers
        .set_index("customer_id")
        .to_dict("index")
    )

    rows = []

    usage_number = 1

    for subscription in subscriptions.itertuples():

        customer = customer_lookup[
            subscription.customer_id
        ]

        start_date = subscription.start_date
        if isinstance(start_date, bytes):
            start_date = start_date.decode("utf-8")
        if not isinstance(start_date, date):
            start_date = pd.to_datetime(str(start_date)).date()

        end_date = subscription.end_date
        if isinstance(end_date, bytes):
            end_date = end_date.decode("utf-8")
        if not isinstance(end_date, date):
            end_date = pd.to_datetime(str(end_date)).date()

        current = max(
            start_date,
            START_DATE,
        )

        final_date = min(
            end_date,
            END_DATE,
        )

        datacenter = random.choice(
            DATACENTERS_BY_REGION[
                customer["region_code"]
            ]
        )

        while current <= final_date:

            segment_multiplier = {
                "SMB": 1.0,
                "Mid-Market": 3.5,
                "Enterprise": 12.0,
                "Strategic": 35.0,
            }[
                customer[
                    "customer_segment"
                ]
            ]

            compute = (
                random.uniform(
                    20,
                    150,
                )
                * segment_multiplier
            )

            storage = (
                random.uniform(
                    100,
                    1500,
                )
                * segment_multiplier
            )

            network = (
                random.uniform(
                    20,
                    500,
                )
                * segment_multiplier
            )

            ai_tokens = 0.0

            if (
                subscription.product_code
                in AI_PRODUCTS
            ):
                ai_tokens = (
                    random.uniform(
                        0.5,
                        30,
                    )
                    * segment_multiplier
                )

            requests = int(
                random.uniform(
                    5_000,
                    100_000,
                )
                * segment_multiplier
            )

            failure_rate = random.uniform(
                0.001,
                0.025,
            )

            failed_requests = int(
                requests
                * failure_rate
            )

            estimated_cost = (
                compute * 0.09
                + storage * 0.002
                + network * 0.01
                + ai_tokens * 2.2
            )

            rows.append(
                {
                    "usage_id":
                        (
                            "USE-"
                            f"{usage_number:010d}"
                        ),

                    "usage_date":
                        current,

                    "customer_id":
                        subscription.customer_id,

                    "product_code":
                        subscription.product_code,

                    "region_code":
                        customer["region_code"],

                    "datacenter_code":
                        datacenter,

                    "compute_hours":
                        round(
                            compute,
                            4,
                        ),

                    "storage_gb":
                        round(
                            storage,
                            4,
                        ),

                    "network_gb":
                        round(
                            network,
                            4,
                        ),

                    "ai_tokens_million":
                        round(
                            ai_tokens,
                            4,
                        ),

                    "requests_count":
                        requests,

                    "failed_requests":
                        failed_requests,

                    "estimated_cost_usd":
                        round(
                            estimated_cost,
                            2,
                        ),

                    "carbon_estimate_kg":
                        round(
                            compute
                            * random.uniform(
                                0.08,
                                0.20,
                            ),
                            4,
                        ),
                }
            )

            usage_number += 1

            current = (
                current
                + pd.DateOffset(
                    months=1
                )
            ).date()

    return pd.DataFrame(rows)

def generate_support_tickets(
    customers: pd.DataFrame,
    usage: pd.DataFrame,
) -> pd.DataFrame:

    usage_summary = (
        usage.groupby(
            "customer_id"
        )
        .agg(
            requests_count=(
                "requests_count",
                "sum",
            ),
            failed_requests=(
                "failed_requests",
                "sum",
            ),
        )
    )

    usage_summary[
        "failure_rate"
    ] = (
        usage_summary[
            "failed_requests"
        ]
        / usage_summary[
            "requests_count"
        ].clip(lower=1)
    )

    rows = []

    ticket_number = 1

    for customer in customers.itertuples():

        failure_rate = 0.005

        if (
            customer.customer_id
            in usage_summary.index
        ):
            failure_rate_value = (
                usage_summary.at[
                    customer.customer_id,
                    "failure_rate",
                ]
            )
            failure_rate = float(
                str(failure_rate_value)
            )

        customer_segment = str(
            customer.customer_segment
        )

        base_tickets = {
            "SMB": 1,
            "Mid-Market": 3,
            "Enterprise": 6,
            "Strategic": 12,
        }[
            customer_segment
        ]

        expected = (
            base_tickets
            * (
                1
                + failure_rate * 30
            )
        )

        ticket_count = int(
            np.random.poisson(
                expected
            )
        )

        for _ in range(ticket_count):

            severity = random.choices(
                [
                    "SEV1",
                    "SEV2",
                    "SEV3",
                    "SEV4",
                ],
                weights=[
                    0.04,
                    0.16,
                    0.45,
                    0.35,
                ],
                k=1,
            )[0]

            sla = {
                "SEV1": 4,
                "SEV2": 8,
                "SEV3": 24,
                "SEV4": 72,
            }[severity]

            resolution_multiplier = (
                1
                + failure_rate * 20
            )

            resolution = (
                random.uniform(
                    0.35,
                    1.65,
                )
                * sla
                * resolution_multiplier
            )

            sla_met = (
                resolution
                <= sla
            )

            csat = (
                random.uniform(
                    4.0,
                    5.0,
                )
                if sla_met
                else random.uniform(
                    1.5,
                    3.8,
                )
            )

            opened = random_date(
                START_DATE,
                END_DATE,
            )

            closed = (
                opened
                + timedelta(
                    days=max(
                        1,
                        int(
                            resolution
                            / 24
                        ),
                    )
                )
            )

            rows.append(
                {
                    "ticket_id":
                        (
                            "TKT-"
                            f"{ticket_number:09d}"
                        ),

                    "customer_id":
                        customer.customer_id,

                    "product_code":
                        random.choice(
                            PRODUCTS
                        ),

                    "opened_date":
                        opened,

                    "closed_date":
                        min(
                            closed,
                            END_DATE,
                        ),

                    "severity":
                        severity,

                    "category":
                        random.choice(
                            [
                                "Availability",
                                "Performance",
                                "Billing",
                                "Security",
                                "Configuration",
                                "Networking",
                                "Database",
                                "AI Service",
                            ]
                        ),

                    "resolution_hours":
                        round(
                            resolution,
                            2,
                        ),

                    "sla_target_hours":
                        sla,

                    "sla_met":
                        sla_met,

                    "reopened":
                        random.random()
                        < (
                            0.05
                            if sla_met
                            else 0.20
                        ),

                    "customer_satisfaction":
                        round(
                            csat,
                            2,
                        ),
                }
            )

            ticket_number += 1

    return pd.DataFrame(rows)

def save_dataset(
    dataframe: pd.DataFrame,
    filename: str,
) -> None:

    path = (
        OUTPUT_DIR
        / filename
    )

    dataframe.to_csv(
        path,
        index=False,
    )

    print(
        f"{filename:<25}"
        f"{len(dataframe):>12,} rows"
    )


def main() -> None:

    print()
    print("=" * 70)
    print(
        "NEXUS 360 ENTERPRISE "
        "DATA GENERATOR"
    )
    print("=" * 70)

    customers = (
        generate_customers()
    )

    subscriptions = (
        generate_subscriptions(
            customers
        )
    )

    revenue = (
        generate_revenue(
            customers,
            subscriptions,
        )
    )

    usage = (
        generate_usage(
            customers,
            subscriptions,
        )
    )

    tickets = (
        generate_support_tickets(
            customers,
            usage,
        )
    )

    save_dataset(
        customers.drop(
            columns=[
                "currency_code",
                "country_name",
            ]
        ),
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

    print("=" * 70)
    print(
        "Generation complete."
    )


if __name__ == "__main__":
    main()