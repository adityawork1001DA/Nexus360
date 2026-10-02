from __future__ import annotations

import pandas as pd

from src.ingestion.api_client import (
    APIClient,
)


FRANKFURTER_RATES_URL = (
    "https://api.frankfurter.dev/v2/rates"
)


def fetch_fx_rates(
    client: APIClient,
    base_currency: str,
    quote_currencies: list[str],
    start_date: str,
    end_date: str,
    force_refresh: bool = False,
) -> pd.DataFrame:

    params = {
        "base":
            base_currency.lower(),

        "quotes":
            ",".join(
                currency.lower()
                for currency
                in quote_currencies
            ),

        "from":
            start_date,

        "to":
            end_date,
    }

    payload = client.get_json(
        url=FRANKFURTER_RATES_URL,
        params=params,
        force_refresh=force_refresh,
    )

    if not isinstance(
        payload,
        list,
    ):
        raise ValueError(
            "Unexpected Frankfurter "
            "response structure."
        )

    rows = []

    for record in payload:

        base = str(
            record["base"]
        ).upper()

        quote = str(
            record["quote"]
        ).upper()

        raw_rate = float(
            record["rate"]
        )

        # ---------------------------------------------------------
        # Warehouse definition:
        #
        # rate_to_usd =
        # USD value of ONE unit of foreign currency.
        #
        # If API gives:
        #     1 USD = 0.85 EUR
        #
        # then:
        #     1 EUR = 1 / 0.85 USD
        # ---------------------------------------------------------

        if base == "USD":

            currency_code = quote

            rate_to_usd = (
                1.0 / raw_rate
            )

        elif quote == "USD":

            currency_code = base

            rate_to_usd = raw_rate

        else:

            continue

        rows.append(
            {
                "rate_date":
                    record["date"],

                "currency_code":
                    currency_code,

                "base_currency":
                    "USD",

                "rate_to_usd":
                    rate_to_usd,

                "source":
                    "Frankfurter",
            }
        )

    dataframe = pd.DataFrame(
        rows
    )

    if dataframe.empty:
        return dataframe

    dataframe[
        "rate_date"
    ] = pd.to_datetime(
        dataframe[
            "rate_date"
        ]
    ).dt.date

    return dataframe