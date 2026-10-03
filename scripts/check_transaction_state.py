from sqlalchemy import text
from src.database.connection import get_engine

engine = get_engine()

with engine.connect() as conn:
    rows = conn.execute(
        text("""
            SELECT
                pid,
                state,
                xact_start,
                wait_event_type,
                wait_event,
                LEFT(query, 120) AS query
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND pid <> pg_backend_pid()
            ORDER BY pid
        """)
    ).mappings().all()

print("=" * 100)
print("POSTGRESQL TRANSACTION STATE")
print("=" * 100)

for row in rows:
    print(
        f"PID={row['pid']} | "
        f"STATE={row['state']} | "
        f"XACT_START={row['xact_start']} | "
        f"WAIT={row['wait_event_type']}/{row['wait_event']}"
    )
    print(f"QUERY={row['query']}")
    print("-" * 100)
