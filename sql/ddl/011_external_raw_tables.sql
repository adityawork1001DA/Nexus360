CREATE TABLE IF NOT EXISTS raw.world_bank_indicators (
    country_code CHAR(3) NOT NULL,

    country_name VARCHAR(150),

    indicator_code VARCHAR(50) NOT NULL,

    indicator_name VARCHAR(200),

    year_number SMALLINT NOT NULL,

    indicator_value NUMERIC(30,8),

    source VARCHAR(50),

    _source_system VARCHAR(50)
        DEFAULT 'world_bank',

    _ingested_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP,

    _run_id BIGINT,

    _record_hash VARCHAR(64),

    PRIMARY KEY (
        country_code,
        indicator_code,
        year_number
    )
);


CREATE TABLE IF NOT EXISTS raw.weather (
    datacenter_code VARCHAR(30)
        NOT NULL,

    weather_date DATE
        NOT NULL,

    mean_temperature_c NUMERIC(8,3),

    max_temperature_c NUMERIC(8,3),

    min_temperature_c NUMERIC(8,3),

    precipitation_mm NUMERIC(12,3),

    wind_speed_kmh NUMERIC(12,3),

    source VARCHAR(50),

    _source_system VARCHAR(50)
        DEFAULT 'open_meteo',

    _ingested_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP,

    _run_id BIGINT,

    _record_hash VARCHAR(64),

    PRIMARY KEY (
        datacenter_code,
        weather_date
    )
);


CREATE TABLE IF NOT EXISTS raw.fx_rates (
    rate_date DATE NOT NULL,

    currency_code CHAR(3) NOT NULL,

    base_currency CHAR(3)
        NOT NULL DEFAULT 'USD',

    rate_to_usd NUMERIC(18,10)
        NOT NULL,

    source VARCHAR(50),

    _source_system VARCHAR(50)
        DEFAULT 'frankfurter',

    _ingested_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP,

    _run_id BIGINT,

    _record_hash VARCHAR(64),

    PRIMARY KEY (
        rate_date,
        currency_code,
        base_currency
    )
);