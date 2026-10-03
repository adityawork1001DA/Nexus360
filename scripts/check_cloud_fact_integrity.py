from sqlalchemy import text
from src.database.connection import get_engine

engine = get_engine()

queries = {
    "total_cloud_fact": """
        SELECT COUNT(*)
        FROM warehouse.fact_cloud_usage
    """,
    "null_usage_id": """
        SELECT COUNT(*)
        FROM warehouse.fact_cloud_usage
        WHERE usage_id IS NULL
    """,
    "non_null_usage_id": """
        SELECT COUNT(*)
        FROM warehouse.fact_cloud_usage
        WHERE usage_id IS NOT NULL
    """,
    "distinct_usage_id": """
        SELECT COUNT(DISTINCT usage_id)
        FROM warehouse.fact_cloud_usage
    """,
    "raw_cloud_usage": """
        SELECT COUNT(*)
        FROM raw.cloud_usage
    """,
    "staging_cloud_usage": """
        SELECT COUNT(*)
        FROM staging.cloud_usage
    """,
}

with engine.connect() as conn:
    print("=" * 80)
    print("NEXUS360 CLOUD FACT INTEGRITY")
    print("=" * 80)

    for name, sql in queries.items():
        value = conn.execute(
            text(sql)
        ).scalar_one()

        print(
            f"{name:<30} {int(value):>15,}"
        )

print("=" * 80)
