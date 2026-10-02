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


def test_world_bank_raw_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM raw.world_bank_indicators
        """
    )

    assert count > 100


def test_weather_raw_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM raw.weather
        """
    )

    assert count > 5000


def test_fx_raw_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM raw.fx_rates
        """
    )

    assert count > 1000


def test_economic_warehouse_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.fact_economic_indicator
        """
    )

    assert count > 100


def test_weather_warehouse_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.fact_weather
        """
    )

    assert count > 5000


def test_fx_warehouse_loaded():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.fact_fx_rate
        """
    )

    assert count > 1000


def test_no_orphan_weather_datacenters():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM warehouse.fact_weather w

        LEFT JOIN
            warehouse.dim_datacenter d
        ON d.datacenter_key =
           w.datacenter_key

        WHERE d.datacenter_key
              IS NULL
        """
    )

    assert count == 0


def test_fx_rates_positive():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM warehouse.fact_fx_rate

        WHERE rate_to_usd <= 0
        """
    )

    assert count == 0


def test_weather_temperature_logic():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM warehouse.fact_weather

        WHERE
            min_temperature_c
            > max_temperature_c
        """
    )

    assert count == 0


def test_world_bank_gdp_exists():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM warehouse.fact_economic_indicator

        WHERE indicator_code =
              'NY.GDP.MKTP.CD'

        AND indicator_value IS NOT NULL
        """
    )

    assert count > 0