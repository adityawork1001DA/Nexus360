-- ============================================================
-- NEXUS 360
-- External RAW -> Warehouse
-- ============================================================


-- ------------------------------------------------------------
-- WORLD BANK
-- ------------------------------------------------------------

INSERT INTO warehouse.fact_economic_indicator (
    country_key,
    indicator_code,
    indicator_name,
    year_number,
    indicator_value,
    source
)

SELECT
    c.country_key,
    r.indicator_code,
    r.indicator_name,
    r.year_number,
    r.indicator_value,
    r.source

FROM raw.world_bank_indicators r

JOIN warehouse.dim_country c
    ON c.country_code =
       r.country_code

ON CONFLICT (
    country_key,
    indicator_code,
    year_number
)

DO UPDATE SET
    indicator_name =
        EXCLUDED.indicator_name,

    indicator_value =
        EXCLUDED.indicator_value,

    source =
        EXCLUDED.source;


-- ------------------------------------------------------------
-- WEATHER
-- ------------------------------------------------------------

INSERT INTO warehouse.fact_weather (
    datacenter_key,
    date_key,
    mean_temperature_c,
    max_temperature_c,
    min_temperature_c,
    precipitation_mm,
    wind_speed_kmh,
    source
)

SELECT
    d.datacenter_key,

    TO_CHAR(
        r.weather_date,
        'YYYYMMDD'
    )::INTEGER,

    r.mean_temperature_c,
    r.max_temperature_c,
    r.min_temperature_c,
    r.precipitation_mm,
    r.wind_speed_kmh,
    r.source

FROM raw.weather r

JOIN warehouse.dim_datacenter d
    ON d.datacenter_code =
       r.datacenter_code

JOIN warehouse.dim_date dt
    ON dt.full_date =
       r.weather_date

ON CONFLICT (
    datacenter_key,
    date_key
)

DO UPDATE SET
    mean_temperature_c =
        EXCLUDED.mean_temperature_c,

    max_temperature_c =
        EXCLUDED.max_temperature_c,

    min_temperature_c =
        EXCLUDED.min_temperature_c,

    precipitation_mm =
        EXCLUDED.precipitation_mm,

    wind_speed_kmh =
        EXCLUDED.wind_speed_kmh,

    source =
        EXCLUDED.source;


-- ------------------------------------------------------------
-- FX
-- ------------------------------------------------------------

INSERT INTO warehouse.fact_fx_rate (
    date_key,
    currency_key,
    base_currency,
    rate_to_usd,
    source
)

SELECT
    TO_CHAR(
        r.rate_date,
        'YYYYMMDD'
    )::INTEGER,

    c.currency_key,

    r.base_currency,

    r.rate_to_usd,

    r.source

FROM raw.fx_rates r

JOIN warehouse.dim_currency c
    ON c.currency_code =
       r.currency_code

JOIN warehouse.dim_date d
    ON d.full_date =
       r.rate_date

ON CONFLICT (
    date_key,
    currency_key,
    base_currency
)

DO UPDATE SET
    rate_to_usd =
        EXCLUDED.rate_to_usd,

    source =
        EXCLUDED.source;