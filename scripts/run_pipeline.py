from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from src.database.connection import get_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DML_DIRECTORY = PROJECT_ROOT / "sql" / "dml"

TRANSFORMATION_FILES = (
    "002_raw_to_staging.sql",
    "003_load_customer_dimension.sql",
    "004_load_subscription_fact.sql",
    "005_load_revenue_fact.sql",
    "006_load_cloud_usage_fact.sql",
    "007_load_support_fact.sql",
    "008_load_external_facts.sql",
)


def execute_sql_file(
    filename: str,
) -> None:

    filepath = DML_DIRECTORY / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Required SQL file not found: {filepath}"
        )

    sql = filepath.read_text(
        encoding="utf-8"
    )

    if not sql.strip():
        raise RuntimeError(
            f"SQL file is empty: {filepath}"
        )

    print()
    print(f"[TRANSFORM] {filename}")

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(sql)
        )

    print(f"[OK]        {filename}")


def run_python_script(
    script_name: str,
    *arguments: str,
) -> None:

    filepath = PROJECT_ROOT / "scripts" / script_name

    if not filepath.exists():
        raise FileNotFoundError(
            f"Required script not found: {filepath}"
        )

    command = [
        sys.executable,
        str(filepath),
        *arguments,
    ]

    print()
    print(
        "[RUN] "
        + " ".join(
            str(part)
            for part in command
        )
    )

    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{script_name} failed with exit code "
            f"{result.returncode}."
        )

    print(
        f"[OK] {script_name}"
    )


def show_propagation_counts() -> None:

    engine = get_engine()

    queries = (
        (
            "RAW customers",
            "SELECT COUNT(*) FROM raw.customers",
        ),
        (
            "Staging customers",
            "SELECT COUNT(*) FROM staging.customers",
        ),
        (
            "Warehouse customers",
            "SELECT COUNT(*) FROM warehouse.dim_customer",
        ),
        (
            "Customer 360",
            "SELECT COUNT(*) FROM analytics.v_customer_360",
        ),
    )

    print()
    print("=" * 72)
    print("CUSTOMER PROPAGATION")
    print("=" * 72)

    with engine.connect() as connection:

        for label, query in queries:

            count = connection.execute(
                text(query)
            ).scalar_one()

            print(
                f"{label:<30} "
                f"{int(count):>12,}"
            )

    print("=" * 72)


def validate_customer_propagation() -> None:

    engine = get_engine()

    with engine.connect() as connection:

        raw_count = int(
            connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM raw.customers"
                )
            ).scalar_one()
        )

        staging_count = int(
            connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM staging.customers"
                )
            ).scalar_one()
        )

        warehouse_count = int(
            connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM warehouse.dim_customer"
                )
            ).scalar_one()
        )

        analytics_count = int(
            connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM analytics.v_customer_360"
                )
            ).scalar_one()
        )

    if not (
        raw_count
        == staging_count
        == warehouse_count
        == analytics_count
    ):
        raise RuntimeError(
            "Customer propagation validation failed. "
            f"RAW={raw_count:,}, "
            f"STAGING={staging_count:,}, "
            f"WAREHOUSE={warehouse_count:,}, "
            f"ANALYTICS={analytics_count:,}."
        )

    print()
    print(
        "[OK] Customer propagation validated: "
        f"{raw_count:,} customers end-to-end."
    )


def refresh_transformations() -> None:

    print()
    print("=" * 72)
    print("NEXUS360 - DATA TRANSFORMATION")
    print("=" * 72)

    for filename in TRANSFORMATION_FILES:
        execute_sql_file(
            filename
        )

    print()
    print(
        "[SUCCESS] Warehouse transformation completed."
    )


def refresh_downstream() -> None:

    run_python_script(
        "build_analytics.py"
    )

    show_propagation_counts()
    validate_customer_propagation()

    run_python_script(
        "predict_current_churn.py"
    )

    run_python_script(
        "build_excel_report.py"
    )


def run_refresh_only() -> None:

    refresh_transformations()
    refresh_downstream()


def run_full_pipeline(
    customers: int,
) -> None:

    if customers < 1:
        raise ValueError(
            "Customer count must be at least 1."
        )

    print()
    print("=" * 72)
    print("NEXUS360 - END-TO-END INCREMENTAL PIPELINE")
    print("=" * 72)

    run_python_script(
        "generate_incremental_enterprise_data.py",
        "--customers",
        str(customers),
    )

    run_python_script(
        "load_synthetic_incremental.py"
    )

    refresh_transformations()
    refresh_downstream()

    print()
    print("=" * 72)
    print(
        "[SUCCESS] NEXUS360 PLATFORM UPDATE COMPLETED"
    )
    print("=" * 72)


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Run the Nexus360 end-to-end data pipeline."
        )
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=1,
        help=(
            "Number of incremental customers to generate "
            "when running the full pipeline."
        ),
    )

    parser.add_argument(
        "--refresh-only",
        action="store_true",
        help=(
            "Do not generate or append new data. "
            "Propagate existing RAW data through staging, "
            "warehouse, analytics, ML and reporting."
        ),
    )

    return parser.parse_args()


def main() -> None:

    args = parse_args()

    if args.refresh_only:
        run_refresh_only()
    else:
        run_full_pipeline(
            customers=args.customers
        )


if __name__ == "__main__":
    main()