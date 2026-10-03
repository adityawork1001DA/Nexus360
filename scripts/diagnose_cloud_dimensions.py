from sqlalchemy import text
from src.database.connection import get_engine

engine = get_engine()

queries = {
    "staging_cloud_rows": """
        SELECT COUNT(*)
        FROM staging.cloud_usage
    """,

    "missing_customer": """
        SELECT COUNT(*)
        FROM staging.cloud_usage s
        LEFT JOIN warehouse.dim_customer c
            ON c.customer_id = s.customer_id
        WHERE c.customer_key IS NULL
    """,

    "missing_product": """
        SELECT COUNT(*)
        FROM staging.cloud_usage s
        LEFT JOIN warehouse.dim_product p
            ON p.product_code = s.product_code
        WHERE p.product_key IS NULL
    """,

    "missing_region": """
        SELECT COUNT(*)
        FROM staging.cloud_usage s
        LEFT JOIN warehouse.dim_region r
            ON r.region_code = s.region_code
        WHERE r.region_key IS NULL
    """,

    "missing_datacenter": """
        SELECT COUNT(*)
        FROM staging.cloud_usage s
        LEFT JOIN warehouse.dim_datacenter d
            ON d.datacenter_code = s.datacenter_code
        WHERE s.datacenter_code IS NOT NULL
          AND d.datacenter_key IS NULL
    """,

    "fully_joinable": """
        SELECT COUNT(*)
        FROM staging.cloud_usage s
        JOIN warehouse.dim_customer c
            ON c.customer_id = s.customer_id
        JOIN warehouse.dim_product p
            ON p.product_code = s.product_code
        JOIN warehouse.dim_region r
            ON r.region_code = s.region_code
    """,
}

with engine.connect() as conn:

    print("=" * 80)
    print("NEXUS360 CLOUD DIMENSION DIAGNOSTIC")
    print("=" * 80)

    for name, sql in queries.items():

        value = conn.execute(
            text(sql)
        ).scalar_one()

        print(
            f"{name:<30} {int(value):>15,}"
        )

    print()
    print("MISSING CUSTOMER IDS")
    print("-" * 80)

    rows = conn.execute(
        text("""
            SELECT
                s.customer_id,
                COUNT(*) AS cloud_rows
            FROM staging.cloud_usage s
            LEFT JOIN warehouse.dim_customer c
                ON c.customer_id = s.customer_id
            WHERE c.customer_key IS NULL
            GROUP BY s.customer_id
            ORDER BY cloud_rows DESC, s.customer_id
            LIMIT 30
        """)
    ).all()

    for customer_id, cloud_rows in rows:
        print(
            f"{customer_id:<30} {int(cloud_rows):>10,}"
        )

    print()
    print("CUSTOMER LAYER COUNTS")
    print("-" * 80)

    layers = {
        "raw.customers": """
            SELECT COUNT(*) FROM raw.customers
        """,
        "staging.customers": """
            SELECT COUNT(*) FROM staging.customers
        """,
        "warehouse.dim_customer": """
            SELECT COUNT(*) FROM warehouse.dim_customer
        """,
    }

    for name, sql in layers.items():

        value = conn.execute(
            text(sql)
        ).scalar_one()

        print(
            f"{name:<30} {int(value):>15,}"
        )

print("=" * 80)
