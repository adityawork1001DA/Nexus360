from pathlib import Path

from sqlalchemy import text

from src.database.connection import get_engine


def execute_sql_file(path: Path) -> None:
    print(f"Running: {path}")

    sql = path.read_text(
        encoding="utf-8"
    )

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(sql)
        )

    print(f"Completed: {path}")


def execute_directory(
    directory: str
) -> None:

    sql_directory = Path(directory)

    files = sorted(
        sql_directory.glob("*.sql")
    )

    if not files:
        print(
            f"No SQL files found in "
            f"{sql_directory}"
        )
        return

    for path in files:
        execute_sql_file(path)


if __name__ == "__main__":

    execute_directory(
        "sql/ddl"
    )

    execute_directory(
        "sql/dml"
    )