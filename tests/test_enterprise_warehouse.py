from sqlalchemy import text

from src.database.connection import (
    get_engine,
)


def scalar(
    query: str,
):
    engine = get_engine()

    with engine.connect() as connection:
        return connection.execute(
            text(query)
        ).scalar_one()


def test_customers_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.dim_customer
        """
    )

    assert count >= 2000


def test_revenue_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.fact_revenue
        """
    )

    assert count > 10000


def test_usage_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.fact_cloud_usage
        """
    )

    assert count > 10000


def test_support_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.fact_support_ticket
        """
    )

    assert count > 1000


def test_revenue_positive():

    revenue = scalar(
        """
        SELECT SUM(
            net_revenue_usd
        )
        FROM warehouse.fact_revenue
        """
    )

    assert revenue > 0


def test_no_orphan_revenue_customers():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM warehouse.fact_revenue f

        LEFT JOIN
            warehouse.dim_customer c
        ON c.customer_key =
           f.customer_key

        WHERE c.customer_key
              IS NULL
        """
    )

    assert count == 0


def test_no_orphan_revenue_products():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM warehouse.fact_revenue f

        LEFT JOIN
            warehouse.dim_product p
        ON p.product_key =
           f.product_key

        WHERE p.product_key
              IS NULL
        """
    )

    assert count == 0