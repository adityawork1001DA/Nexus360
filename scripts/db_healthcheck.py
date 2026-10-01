from sqlalchemy import text

from src.database.connection import get_engine


CHECKS = {
    "Database connection":
        "SELECT 1",

    "Date dimension":
        """
        SELECT COUNT(*)
        FROM warehouse.dim_date
        """,

    "Products":
        """
        SELECT COUNT(*)
        FROM warehouse.dim_product
        """,

    "Currencies":
        """
        SELECT COUNT(*)
        FROM warehouse.dim_currency
        """,

    "Regions":
        """
        SELECT COUNT(*)
        FROM warehouse.dim_region
        """,
}


def main() -> None:

    engine = get_engine()

    print()
    print("=" * 60)
    print(
        "NEXUS 360 DATABASE HEALTH CHECK"
    )
    print("=" * 60)

    with engine.connect() as connection:

        for name, query in CHECKS.items():

            try:
                result = connection.execute(
                    text(query)
                ).scalar()

                print(
                    f"[OK] {name:<25} "
                    f"{result}"
                )

            except Exception as exc:

                print(
                    f"[FAIL] {name:<25} "
                    f"{exc}"
                )

    print("=" * 60)


if __name__ == "__main__":
    main()