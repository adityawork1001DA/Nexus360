from sqlalchemy import text

from src.database.connection import (
    get_engine,
)
from src.ingestion.reference_data import (
    COUNTRIES,
)


def main() -> None:

    engine = get_engine()

    query = text(
        """
        INSERT INTO warehouse.dim_country (
            country_code,
            country_name,
            world_bank_code,
            currency_code
        )
        VALUES (
            :country_code,
            :country_name,
            :world_bank_code,
            :currency_code
        )

        ON CONFLICT (country_code)

        DO UPDATE SET
            country_name =
                EXCLUDED.country_name,

            world_bank_code =
                EXCLUDED.world_bank_code,

            currency_code =
                EXCLUDED.currency_code
        """
    )

    with engine.begin() as connection:

        for (
            country_code,
            country_name,
            region_code,
            currency_code,
        ) in COUNTRIES:

            connection.execute(
                query,
                {
                    "country_code":
                        country_code,

                    "country_name":
                        country_name,

                    "world_bank_code":
                        country_code,

                    "currency_code":
                        currency_code,
                },
            )

    print(
        f"Loaded {len(COUNTRIES)} "
        "countries."
    )


if __name__ == "__main__":
    main()