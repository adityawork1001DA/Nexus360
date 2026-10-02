from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from src.database.connection import get_engine


# ============================================================
# NEXUS 360
# Analytics Semantic Layer Builder
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ANALYTICS_DIRECTORY = (
    PROJECT_ROOT
    / "sql"
    / "analytics"
)


def discover_sql_files() -> list[Path]:
    """
    Discover all SQL files inside sql/analytics recursively.

    Files are executed in deterministic lexical order.
    """

    if not ANALYTICS_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Analytics directory not found: "
            f"{ANALYTICS_DIRECTORY}"
        )

    sql_files = sorted(
        ANALYTICS_DIRECTORY.rglob("*.sql")
    )

    if not sql_files:
        raise FileNotFoundError(
            f"No SQL files found inside: "
            f"{ANALYTICS_DIRECTORY}"
        )

    return sql_files


def execute_sql_file(
    filepath: Path,
) -> None:
    """
    Execute one analytics SQL file inside
    a database transaction.
    """

    sql = filepath.read_text(
        encoding="utf-8"
    )

    if not sql.strip():
        print(
            f"[SKIP] Empty SQL file: "
            f"{filepath.relative_to(PROJECT_ROOT)}"
        )
        return

    relative_path = filepath.relative_to(
        PROJECT_ROOT
    )

    print(
        f"[BUILD] {relative_path}"
    )

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(sql)
        )

    print(
        f"[OK]    {relative_path}"
    )


def main() -> None:
    """
    Build the complete NEXUS 360 analytics
    semantic layer.
    """

    print()
    print("=" * 72)
    print(
        "NEXUS 360 - ANALYTICS SEMANTIC LAYER BUILD"
    )
    print("=" * 72)

    sql_files = discover_sql_files()

    print(
        f"Discovered {len(sql_files)} "
        f"analytics SQL files."
    )
    print()

    completed = 0
    failed = 0

    for filepath in sql_files:

        try:
            execute_sql_file(
                filepath
            )

            completed += 1

        except Exception as exc:

            failed += 1

            print()
            print(
                f"[FAILED] "
                f"{filepath.relative_to(PROJECT_ROOT)}"
            )

            print(
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print()
            print("=" * 72)
            print(
                "ANALYTICS BUILD FAILED"
            )
            print("=" * 72)

            raise

    print()
    print("=" * 72)

    print(
        "NEXUS 360 ANALYTICS BUILD SUMMARY"
    )

    print("-" * 72)

    print(
        f"SQL files discovered : "
        f"{len(sql_files)}"
    )

    print(
        f"Successfully executed : "
        f"{completed}"
    )

    print(
        f"Failed                : "
        f"{failed}"
    )

    print("-" * 72)

    if failed == 0:
        print(
            "[SUCCESS] Analytics semantic "
            "layer built successfully."
        )

    print("=" * 72)
    print()


if __name__ == "__main__":
    main()