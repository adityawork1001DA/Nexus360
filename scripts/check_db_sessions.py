from sqlalchemy import text
from src.database.connection import get_engine

engine = get_engine()

sql = """
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    NOW() - query_start AS running_for,
    LEFT(query, 250) AS query
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid <> pg_backend_pid()
ORDER BY query_start;
"""

with engine.connect() as conn:
    rows = conn.execute(text(sql)).mappings().all()

print("=" * 100)
print("NEXUS360 POSTGRESQL ACTIVE SESSIONS")
print("=" * 100)

for row in rows:
    print()
    for key, value in row.items():
        print(f"{key:<18}: {value}")
