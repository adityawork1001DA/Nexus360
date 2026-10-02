from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.database.audit import (
    finish_pipeline_run,
    start_pipeline_run,
)
from src.database.connection import (
    get_engine,
)
from src.ingestion.api_client import (
    APIClient,
)
from src.ingestion.frankfurter import (
    fetch_fx_rates,
)
from src.ingestion.open_meteo import (
    fetch_datacenter_weather,
)
from src.ingestion.world_bank import (
    fetch_world_bank_data,
)
from src.ingestion.reference_data import (
    COUNTRIES,
)
from src.utils.hashing import (
    create_record_hash,
)


OUTPUT_DIR = Path(
    "data/raw/external"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


WORLD_BANK_START_YEAR = 2021
WORLD_BANK_END_YEAR = 2025

WEATHER_START_DATE = "2023-01-01"
WEATHER_END_DATE = "2025-12-31"

FX_START_DATE = "2023-01-01"
FX_END_DATE = "2025-12-31"


FX_CURRENCIES = [
    "EUR",
    "GBP",
    "INR",
    "JPY",
    "CAD",
    "AUD",
    "SGD",
    "BRL",
    "AED",
]


def add_metadata(
    dataframe: pd.DataFrame,
    run_id: int,
    source_system: str,
) -> pd.DataFrame:

    dataframe = dataframe.copy()

    business_columns = list(
        dataframe.columns
    )

    dataframe[
        "_record_hash"
    ] = dataframe[
        business_columns
    ].apply(
        lambda row:
            create_record_hash(
                row.tolist()
            ),
        axis=1,
    )

    dataframe[
        "_source_system"
    ] = source_system

    dataframe[
        "_run_id"
    ] = run_id

    return dataframe


def replace_raw_table(
    dataframe: pd.DataFrame,
    table_name: str,
) -> None:

    engine = get_engine()

    with engine.begin() as connection:

        connection.execute(
            text(
                f"TRUNCATE TABLE "
                f"raw.{table_name}"
            )
        )

    dataframe.to_sql(
        name=table_name,
        schema="raw",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=250,
    )


def ingest_world_bank(
    client: APIClient,
) -> None:

    engine = get_engine()

    run_id = start_pipeline_run(
        engine=engine,
        pipeline_name=(
            "external_world_bank"
        ),
        source_name="World Bank",
    )

    try:

        country_codes = [
            country[0]
            for country
            in COUNTRIES
        ]

        dataframe = (
            fetch_world_bank_data(
                client=client,
                country_codes=(
                    country_codes
                ),
                start_year=(
                    WORLD_BANK_START_YEAR
                ),
                end_year=(
                    WORLD_BANK_END_YEAR
                ),
            )
        )

        dataframe = add_metadata(
            dataframe=dataframe,
            run_id=run_id,
            source_system="world_bank",
        )

        dataframe.to_csv(
            OUTPUT_DIR
            / "world_bank_indicators.csv",
            index=False,
        )

        replace_raw_table(
            dataframe=dataframe,
            table_name=(
                "world_bank_indicators"
            ),
        )

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="SUCCESS",
            rows_read=len(dataframe),
            rows_inserted=len(dataframe),
            metadata={
                "start_year":
                    WORLD_BANK_START_YEAR,

                "end_year":
                    WORLD_BANK_END_YEAR,
            },
        )

        print(
            f"[OK] World Bank: "
            f"{len(dataframe):,} rows"
        )

    except Exception as exc:

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="FAILED",
            error_message=(
                f"{type(exc).__name__}: "
                f"{str(exc)[:2000]}"
            ),
        )

        raise


def get_datacenters() -> list[dict]:

    engine = get_engine()

    query = text(
        """
        SELECT
            datacenter_code,
            latitude,
            longitude

        FROM warehouse.dim_datacenter

        WHERE active_flag = TRUE

        ORDER BY datacenter_code
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query
        ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


def ingest_weather(
    client: APIClient,
) -> None:

    engine = get_engine()

    run_id = start_pipeline_run(
        engine=engine,
        pipeline_name=(
            "external_weather"
        ),
        source_name="Open-Meteo",
    )

    try:

        frames = []

        datacenters = (
            get_datacenters()
        )

        for datacenter in datacenters:

            code = datacenter[
                "datacenter_code"
            ]

            print(
                f"[WEATHER] {code}"
            )

            frame = (
                fetch_datacenter_weather(
                    client=client,

                    datacenter_code=code,

                    latitude=float(
                        datacenter[
                            "latitude"
                        ]
                    ),

                    longitude=float(
                        datacenter[
                            "longitude"
                        ]
                    ),

                    start_date=(
                        WEATHER_START_DATE
                    ),

                    end_date=(
                        WEATHER_END_DATE
                    ),
                )
            )

            frames.append(frame)

        dataframe = pd.concat(
            frames,
            ignore_index=True,
        )

        dataframe = add_metadata(
            dataframe=dataframe,
            run_id=run_id,
            source_system="open_meteo",
        )

        dataframe.to_csv(
            OUTPUT_DIR
            / "weather.csv",
            index=False,
        )

        replace_raw_table(
            dataframe=dataframe,
            table_name="weather",
        )

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="SUCCESS",
            rows_read=len(dataframe),
            rows_inserted=len(dataframe),
            metadata={
                "datacenters":
                    len(datacenters),

                "start_date":
                    WEATHER_START_DATE,

                "end_date":
                    WEATHER_END_DATE,
            },
        )

        print(
            f"[OK] Open-Meteo: "
            f"{len(dataframe):,} rows"
        )

    except Exception as exc:

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="FAILED",
            error_message=(
                f"{type(exc).__name__}: "
                f"{str(exc)[:2000]}"
            ),
        )

        raise


def ingest_fx(
    client: APIClient,
) -> None:

    engine = get_engine()

    run_id = start_pipeline_run(
        engine=engine,
        pipeline_name=(
            "external_fx"
        ),
        source_name="Frankfurter",
    )

    try:

        dataframe = fetch_fx_rates(
            client=client,
            base_currency="USD",
            quote_currencies=(
                FX_CURRENCIES
            ),
            start_date=FX_START_DATE,
            end_date=FX_END_DATE,
        )

        dataframe = add_metadata(
            dataframe=dataframe,
            run_id=run_id,
            source_system=(
                "frankfurter"
            ),
        )

        dataframe.to_csv(
            OUTPUT_DIR
            / "fx_rates.csv",
            index=False,
        )

        replace_raw_table(
            dataframe=dataframe,
            table_name="fx_rates",
        )

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="SUCCESS",
            rows_read=len(dataframe),
            rows_inserted=len(dataframe),
            metadata={
                "base_currency":
                    "USD",

                "currencies":
                    FX_CURRENCIES,

                "start_date":
                    FX_START_DATE,

                "end_date":
                    FX_END_DATE,
            },
        )

        print(
            f"[OK] Frankfurter: "
            f"{len(dataframe):,} rows"
        )

    except Exception as exc:

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="FAILED",
            error_message=(
                f"{type(exc).__name__}: "
                f"{str(exc)[:2000]}"
            ),
        )

        raise


def main() -> None:

    print()
    print("=" * 70)
    print(
        "NEXUS 360 - EXTERNAL DATA INGESTION"
    )
    print("=" * 70)

    client = APIClient(
        timeout_seconds=30,
        cache_enabled=True,
        cache_directory=(
            "data/cache/api"
        ),
    )

    ingest_world_bank(
        client
    )

    ingest_weather(
        client
    )

    ingest_fx(
        client
    )

    print()
    print("=" * 70)
    print(
        "External ingestion completed."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()