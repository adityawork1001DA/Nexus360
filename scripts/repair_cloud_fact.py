from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_engine


# ============================================================
# NEXUS360
# One-time Cloud Fact Integrity Repair
# ============================================================

LOCK_ID = 360006


def scalar(
    connection,
    sql: str,
) -> int:
    """
    Execute a scalar COUNT-style query and return int.
    """

    value = connection.execute(
        text(sql)
    ).scalar_one()

    return int(value)


def main() -> None:
    engine = get_engine()

    print()
    print("=" * 78)
    print("NEXUS360 - CLOUD FACT REPAIR")
    print("=" * 78)
    print()
    print(
        "This repair does NOT modify raw.cloud_usage."
    )
    print(
        "staging.cloud_usage and "
        "warehouse.fact_cloud_usage will be rebuilt "
        "from the current RAW source."
    )
    print()

    # --------------------------------------------------------
    # Dedicated connection owns the session advisory lock.
    #
    # We intentionally do NOT use this connection for the
    # repair transaction. This avoids SQLAlchemy autobegin /
    # nested transaction conflicts.
    # --------------------------------------------------------

    lock_connection = engine.connect()

    try:
        locked = lock_connection.execute(
            text(
                """
                SELECT pg_try_advisory_lock(:lock_id)
                """
            ),
            {
                "lock_id": LOCK_ID,
            },
        ).scalar_one()

        # End the SQLAlchemy transaction created by the
        # advisory-lock SELECT. PostgreSQL session-level
        # advisory lock remains held by this connection.
        lock_connection.commit()

        if not locked:
            raise RuntimeError(
                "Another Nexus360 cloud repair or pipeline "
                "operation is already running."
            )

        print(
            "[OK] Exclusive Nexus360 cloud repair lock acquired."
        )
        print()

        # ----------------------------------------------------
        # PRE-REPAIR VALIDATION
        # ----------------------------------------------------

        with engine.connect() as check_connection:

            raw_count = scalar(
                check_connection,
                """
                SELECT COUNT(*)
                FROM raw.cloud_usage
                """,
            )

            raw_unique = scalar(
                check_connection,
                """
                SELECT COUNT(DISTINCT usage_id)
                FROM raw.cloud_usage
                """,
            )

            raw_null = scalar(
                check_connection,
                """
                SELECT COUNT(*)
                FROM raw.cloud_usage
                WHERE usage_id IS NULL
                """,
            )

            warehouse_before = scalar(
                check_connection,
                """
                SELECT COUNT(*)
                FROM warehouse.fact_cloud_usage
                """,
            )

            null_before = scalar(
                check_connection,
                """
                SELECT COUNT(*)
                FROM warehouse.fact_cloud_usage
                WHERE usage_id IS NULL
                """,
            )

        print(
            f"RAW rows                 : "
            f"{raw_count:,}"
        )

        print(
            f"RAW unique usage IDs     : "
            f"{raw_unique:,}"
        )

        print(
            f"RAW NULL usage IDs       : "
            f"{raw_null:,}"
        )

        print(
            f"Warehouse rows before    : "
            f"{warehouse_before:,}"
        )

        print(
            f"Warehouse NULL IDs before: "
            f"{null_before:,}"
        )

        print()

        # ----------------------------------------------------
        # RAW SAFETY CHECKS
        # ----------------------------------------------------

        if raw_count <= 0:
            raise RuntimeError(
                "raw.cloud_usage is empty. "
                "Repair aborted."
            )

        if raw_null != 0:
            raise RuntimeError(
                "raw.cloud_usage contains NULL usage_id "
                "values. Repair aborted."
            )

        if raw_count != raw_unique:
            raise RuntimeError(
                "raw.cloud_usage contains duplicate "
                "usage_id values. Repair aborted."
            )

        # ----------------------------------------------------
        # ATOMIC REPAIR TRANSACTION
        # ----------------------------------------------------

        print(
            "[1/3] Rebuilding staging.cloud_usage..."
        )

        with engine.begin() as repair_connection:

            # ------------------------------------------------
            # STAGING
            # ------------------------------------------------

            repair_connection.execute(
                text(
                    """
                    TRUNCATE TABLE staging.cloud_usage;
                    """
                )
            )

            repair_connection.execute(
                text(
                    """
                    INSERT INTO staging.cloud_usage
                    SELECT *
                    FROM raw.cloud_usage
                    WHERE
                        usage_id IS NOT NULL
                        AND usage_date IS NOT NULL
                        AND customer_id IS NOT NULL
                        AND compute_hours >= 0
                        AND storage_gb >= 0
                        AND network_gb >= 0;
                    """
                )
            )

            staging_count = scalar(
                repair_connection,
                """
                SELECT COUNT(*)
                FROM staging.cloud_usage
                """,
            )

            print(
                f"[OK] Staging rows prepared: "
                f"{staging_count:,}"
            )

            if staging_count != raw_count:
                raise RuntimeError(
                    "Staging cloud count does not equal RAW. "
                    f"RAW={raw_count:,}, "
                    f"STAGING={staging_count:,}. "
                    "Transaction will be rolled back."
                )

            # ------------------------------------------------
            # WAREHOUSE
            # ------------------------------------------------

            print()
            print(
                "[2/3] Rebuilding "
                "warehouse.fact_cloud_usage..."
            )

            repair_connection.execute(
                text(
                    """
                    TRUNCATE TABLE
                        warehouse.fact_cloud_usage
                    RESTART IDENTITY;
                    """
                )
            )

            repair_connection.execute(
                text(
                    """
                    INSERT INTO warehouse.fact_cloud_usage (
                        usage_id,
                        date_key,
                        customer_key,
                        product_key,
                        region_key,
                        datacenter_key,
                        compute_hours,
                        storage_gb,
                        network_gb,
                        ai_tokens_million,
                        requests_count,
                        failed_requests,
                        estimated_cost_usd,
                        carbon_estimate_kg
                    )

                    SELECT
                        s.usage_id,

                        TO_CHAR(
                            s.usage_date,
                            'YYYYMMDD'
                        )::INTEGER,

                        c.customer_key,
                        p.product_key,
                        r.region_key,
                        dc.datacenter_key,

                        s.compute_hours,
                        s.storage_gb,
                        s.network_gb,
                        s.ai_tokens_million,
                        s.requests_count,
                        s.failed_requests,
                        s.estimated_cost_usd,
                        s.carbon_estimate_kg

                    FROM staging.cloud_usage s

                    JOIN warehouse.dim_customer c
                        ON c.customer_id =
                           s.customer_id

                    JOIN warehouse.dim_product p
                        ON p.product_code =
                           s.product_code

                    JOIN warehouse.dim_region r
                        ON r.region_code =
                           s.region_code

                    LEFT JOIN warehouse.dim_datacenter dc
                        ON dc.datacenter_code =
                           s.datacenter_code;
                    """
                )
            )

            warehouse_after = scalar(
                repair_connection,
                """
                SELECT COUNT(*)
                FROM warehouse.fact_cloud_usage
                """,
            )

            unique_after = scalar(
                repair_connection,
                """
                SELECT COUNT(DISTINCT usage_id)
                FROM warehouse.fact_cloud_usage
                """,
            )

            null_after = scalar(
                repair_connection,
                """
                SELECT COUNT(*)
                FROM warehouse.fact_cloud_usage
                WHERE usage_id IS NULL
                """,
            )

            print(
                f"[OK] Warehouse rows prepared: "
                f"{warehouse_after:,}"
            )

            # ------------------------------------------------
            # VALIDATION BEFORE COMMIT
            # ------------------------------------------------

            print()
            print(
                "[3/3] Validating repaired cloud fact..."
            )
            print()
            print("-" * 78)

            print(
                f"RAW                       "
                f"{raw_count:>15,}"
            )

            print(
                f"STAGING                   "
                f"{staging_count:>15,}"
            )

            print(
                f"WAREHOUSE                 "
                f"{warehouse_after:>15,}"
            )

            print(
                f"WAREHOUSE UNIQUE IDs      "
                f"{unique_after:>15,}"
            )

            print(
                f"WAREHOUSE NULL IDs        "
                f"{null_after:>15,}"
            )

            print("-" * 78)

            if warehouse_after != staging_count:
                raise RuntimeError(
                    "Cloud repair validation failed. "
                    "Warehouse count differs from staging. "
                    "Transaction will be rolled back."
                )

            if unique_after != warehouse_after:
                raise RuntimeError(
                    "Cloud repair validation failed. "
                    "usage_id is not unique. "
                    "Transaction will be rolled back."
                )

            if null_after != 0:
                raise RuntimeError(
                    "Cloud repair validation failed. "
                    "NULL usage_id remains. "
                    "Transaction will be rolled back."
                )

            if warehouse_after != raw_count:
                raise RuntimeError(
                    "Cloud repair validation failed. "
                    "Not every RAW cloud record reached "
                    "the warehouse. "
                    "Transaction will be rolled back."
                )

            # engine.begin() commits automatically here
            # only if every validation above succeeded.

        print()
        print(
            "[COMMIT] Cloud repair transaction committed."
        )

        # ----------------------------------------------------
        # POST-COMMIT VERIFICATION
        # ----------------------------------------------------

        with engine.connect() as verify_connection:

            final_staging = scalar(
                verify_connection,
                """
                SELECT COUNT(*)
                FROM staging.cloud_usage
                """,
            )

            final_warehouse = scalar(
                verify_connection,
                """
                SELECT COUNT(*)
                FROM warehouse.fact_cloud_usage
                """,
            )

            final_unique = scalar(
                verify_connection,
                """
                SELECT COUNT(DISTINCT usage_id)
                FROM warehouse.fact_cloud_usage
                """,
            )

            final_null = scalar(
                verify_connection,
                """
                SELECT COUNT(*)
                FROM warehouse.fact_cloud_usage
                WHERE usage_id IS NULL
                """,
            )

        print()
        print("=" * 78)
        print("POST-COMMIT VERIFICATION")
        print("=" * 78)

        print(
            f"RAW                       "
            f"{raw_count:>15,}"
        )

        print(
            f"STAGING                   "
            f"{final_staging:>15,}"
        )

        print(
            f"WAREHOUSE                 "
            f"{final_warehouse:>15,}"
        )

        print(
            f"WAREHOUSE UNIQUE IDs      "
            f"{final_unique:>15,}"
        )

        print(
            f"WAREHOUSE NULL IDs        "
            f"{final_null:>15,}"
        )

        if not (
            raw_count
            == final_staging
            == final_warehouse
            == final_unique
        ):
            raise RuntimeError(
                "Post-commit cloud count verification failed."
            )

        if final_null != 0:
            raise RuntimeError(
                "Post-commit NULL usage_id verification failed."
            )

        print()
        print(
            "[SUCCESS] Cloud fact is clean, unique "
            "and synchronized with RAW."
        )

    finally:

        # ----------------------------------------------------
        # RELEASE SESSION-LEVEL ADVISORY LOCK
        # ----------------------------------------------------

        try:
            lock_connection.execute(
                text(
                    """
                    SELECT pg_advisory_unlock(:lock_id)
                    """
                ),
                {
                    "lock_id": LOCK_ID,
                },
            )

            lock_connection.commit()

        finally:
            lock_connection.close()

    print()
    print("=" * 78)
    print()


if __name__ == "__main__":
    main()