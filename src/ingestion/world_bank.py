from __future__ import annotations

from typing import Any

import pandas as pd

from src.ingestion.api_client import (
    APIClient,
)


WORLD_BANK_BASE_URL = (
    "https://api.worldbank.org/v2"
)


INDICATORS = {
    "NY.GDP.MKTP.CD":
        "GDP current USD",

    "SP.POP.TOTL":
        "Population total",

    "NY.GDP.PCAP.CD":
        "GDP per capita current USD",

    "IT.NET.USER.ZS":
        "Individuals using Internet percent",

    "FP.CPI.TOTL.ZG":
        "Inflation consumer prices annual percent",
}


def fetch_indicator(
    client: APIClient,
    country_codes: list[str],
    indicator_code: str,
    start_year: int,
    end_year: int,
    force_refresh: bool = False,
) -> pd.DataFrame:

    countries = ";".join(
        country_codes
    )

    url = (
        f"{WORLD_BANK_BASE_URL}"
        f"/country/{countries}"
        f"/indicator/{indicator_code}"
    )

    params: dict[str, Any] = {
        "format": "json",
        "date": (
            f"{start_year}:"
            f"{end_year}"
        ),
        "per_page": 20000,
    }

    payload = client.get_json(
        url=url,
        params=params,
        force_refresh=force_refresh,
    )

    if (
        not isinstance(payload, list)
        or len(payload) < 2
    ):
        raise ValueError(
            "Unexpected World Bank "
            "API response structure."
        )

    records = payload[1]

    if records is None:
        return pd.DataFrame()

    rows = []

    for record in records:

        country = record.get(
            "country"
        ) or {}

        rows.append(
            {
                "country_code":
                    record.get(
                        "countryiso3code"
                    ),

                "country_name":
                    country.get(
                        "value"
                    ),

                "indicator_code":
                    indicator_code,

                "indicator_name":
                    INDICATORS.get(
                        indicator_code,
                        indicator_code,
                    ),

                "year_number":
                    int(
                        record["date"]
                    ),

                "indicator_value":
                    record.get(
                        "value"
                    ),

                "source":
                    "World Bank",
            }
        )

    return pd.DataFrame(rows)


def fetch_world_bank_data(
    client: APIClient,
    country_codes: list[str],
    start_year: int = 2021,
    end_year: int = 2025,
    force_refresh: bool = False,
) -> pd.DataFrame:

    frames = []

    for (
        indicator_code,
        indicator_name,
    ) in INDICATORS.items():

        print(
            f"[WORLD BANK] "
            f"{indicator_name}"
        )

        frame = fetch_indicator(
            client=client,
            country_codes=country_codes,
            indicator_code=indicator_code,
            start_year=start_year,
            end_year=end_year,
            force_refresh=force_refresh,
        )

        if not frame.empty:
            frames.append(frame)

    if not frames:
        return pd.DataFrame()

    dataframe = pd.concat(
        frames,
        ignore_index=True,
    )

    dataframe[
        "indicator_value"
    ] = pd.to_numeric(
        dataframe[
            "indicator_value"
        ],
        errors="coerce",
    )

    return dataframe