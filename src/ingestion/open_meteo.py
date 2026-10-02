from __future__ import annotations

import pandas as pd

from src.ingestion.api_client import (
    APIClient,
)


OPEN_METEO_URL = (
    "https://archive-api.open-meteo.com"
    "/v1/archive"
)


DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
]


def fetch_datacenter_weather(
    client: APIClient,
    datacenter_code: str,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    force_refresh: bool = False,
) -> pd.DataFrame:

    params = {
        "latitude":
            latitude,

        "longitude":
            longitude,

        "start_date":
            start_date,

        "end_date":
            end_date,

        "daily":
            ",".join(
                DAILY_VARIABLES
            ),

        "timezone":
            "auto",
    }

    payload = client.get_json(
        url=OPEN_METEO_URL,
        params=params,
        force_refresh=force_refresh,
    )

    daily = payload.get(
        "daily"
    )

    if not daily:

        raise ValueError(
            "Open-Meteo response "
            "contains no daily data."
        )

    dataframe = pd.DataFrame(
        {
            "weather_date":
                daily["time"],

            "mean_temperature_c":
                daily[
                    "temperature_2m_mean"
                ],

            "max_temperature_c":
                daily[
                    "temperature_2m_max"
                ],

            "min_temperature_c":
                daily[
                    "temperature_2m_min"
                ],

            "precipitation_mm":
                daily[
                    "precipitation_sum"
                ],

            "wind_speed_kmh":
                daily[
                    "wind_speed_10m_max"
                ],
        }
    )

    dataframe[
        "datacenter_code"
    ] = datacenter_code

    dataframe[
        "source"
    ] = "Open-Meteo"

    dataframe[
        "weather_date"
    ] = pd.to_datetime(
        dataframe[
            "weather_date"
        ]
    ).dt.date

    return dataframe