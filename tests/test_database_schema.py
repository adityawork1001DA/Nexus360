from sqlalchemy import inspect, text

from src.database.connection import get_engine


EXPECTED_SCHEMAS = {
    "raw",
    "staging",
    "warehouse",
    "analytics",
    "ml",
    "audit",
}


def test_required_schemas_exist():
    engine = get_engine()
    inspector = inspect(engine)

    schemas = set(
        inspector.get_schema_names()
    )

    missing = (
        EXPECTED_SCHEMAS - schemas
    )

    assert not missing, (
        f"Missing schemas: {missing}"
    )


def test_date_dimension_populated():
    engine = get_engine()

    query = text(
        """
        SELECT COUNT(*)
        FROM warehouse.dim_date
        """
    )

    with engine.connect() as connection:
        count = connection.execute(
            query
        ).scalar_one()

    assert count > 4000


def test_products_exist():
    engine = get_engine()

    query = text(
        """
        SELECT COUNT(*)
        FROM warehouse.dim_product
        """
    )

    with engine.connect() as connection:
        count = connection.execute(
            query
        ).scalar_one()

    assert count >= 10


def test_currencies_exist():
    engine = get_engine()

    query = text(
        """
        SELECT COUNT(*)
        FROM warehouse.dim_currency
        """
    )

    with engine.connect() as connection:
        count = connection.execute(
            query
        ).scalar_one()

    assert count >= 10