CREATE TABLE IF NOT EXISTS warehouse.fact_subscription (
    subscription_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    subscription_id VARCHAR(40)
        NOT NULL UNIQUE,

    customer_key BIGINT NOT NULL
        REFERENCES warehouse.dim_customer(customer_key),

    product_key BIGINT NOT NULL
        REFERENCES warehouse.dim_product(product_key),

    start_date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),

    end_date_key INTEGER
        REFERENCES warehouse.dim_date(date_key),

    billing_frequency VARCHAR(20)
        CHECK (
            billing_frequency IN (
                'Monthly',
                'Quarterly',
                'Annual'
            )
        ),

    contract_value_usd NUMERIC(18,2)
        CHECK (contract_value_usd >= 0),

    seats INTEGER
        CHECK (seats >= 0),

    subscription_status VARCHAR(20)
        CHECK (
            subscription_status IN (
                'Active',
                'Cancelled',
                'Expired',
                'Trial'
            )
        ),

    auto_renew BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.fact_revenue (
    revenue_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    transaction_id VARCHAR(50)
        NOT NULL UNIQUE,

    date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),

    customer_key BIGINT NOT NULL
        REFERENCES warehouse.dim_customer(customer_key),

    product_key BIGINT NOT NULL
        REFERENCES warehouse.dim_product(product_key),

    region_key BIGINT NOT NULL
        REFERENCES warehouse.dim_region(region_key),

    currency_key BIGINT NOT NULL
        REFERENCES warehouse.dim_currency(currency_key),

    quantity NUMERIC(18,4)
        CHECK (quantity >= 0),

    gross_revenue_local NUMERIC(18,2)
        NOT NULL,

    discount_local NUMERIC(18,2)
        NOT NULL DEFAULT 0,

    net_revenue_local NUMERIC(18,2)
        NOT NULL,

    fx_rate_to_usd NUMERIC(18,8)
        NOT NULL,

    net_revenue_usd NUMERIC(18,2)
        NOT NULL,

    estimated_cost_usd NUMERIC(18,2),

    gross_profit_usd NUMERIC(18,2),

    revenue_type VARCHAR(30),

    loaded_at TIMESTAMPTZ
        NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS warehouse.fact_cloud_usage (
    usage_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    usage_id VARCHAR(50) UNIQUE,

    date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),

    customer_key BIGINT NOT NULL
        REFERENCES warehouse.dim_customer(customer_key),

    product_key BIGINT NOT NULL
        REFERENCES warehouse.dim_product(product_key),

    region_key BIGINT NOT NULL
        REFERENCES warehouse.dim_region(region_key),

    datacenter_key BIGINT
        REFERENCES warehouse.dim_datacenter(datacenter_key),

    compute_hours NUMERIC(18,4)
        DEFAULT 0,

    storage_gb NUMERIC(18,4)
        DEFAULT 0,

    network_gb NUMERIC(18,4)
        DEFAULT 0,

    ai_tokens_million NUMERIC(18,4)
        DEFAULT 0,

    requests_count BIGINT
        DEFAULT 0,

    failed_requests BIGINT
        DEFAULT 0,

    estimated_cost_usd NUMERIC(18,2)
        DEFAULT 0,

    carbon_estimate_kg NUMERIC(18,4),

    loaded_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS warehouse.fact_support_ticket (
    ticket_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    ticket_id VARCHAR(40)
        NOT NULL UNIQUE,

    customer_key BIGINT NOT NULL
        REFERENCES warehouse.dim_customer(customer_key),

    product_key BIGINT
        REFERENCES warehouse.dim_product(product_key),

    opened_date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),

    closed_date_key INTEGER
        REFERENCES warehouse.dim_date(date_key),

    severity VARCHAR(10)
        CHECK (
            severity IN (
                'SEV1',
                'SEV2',
                'SEV3',
                'SEV4'
            )
        ),

    category VARCHAR(100),

    resolution_hours NUMERIC(12,2),

    sla_target_hours NUMERIC(12,2),

    sla_met BOOLEAN,

    reopened BOOLEAN DEFAULT FALSE,

    customer_satisfaction NUMERIC(3,2)
        CHECK (
            customer_satisfaction
            BETWEEN 1 AND 5
        )
);


CREATE TABLE IF NOT EXISTS warehouse.fact_fx_rate (
    fx_rate_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),

    currency_key BIGINT NOT NULL
        REFERENCES warehouse.dim_currency(currency_key),

    base_currency CHAR(3)
        NOT NULL DEFAULT 'USD',

    rate_to_usd NUMERIC(18,8)
        NOT NULL,

    source VARCHAR(50)
        NOT NULL DEFAULT 'Frankfurter',

    UNIQUE (
        date_key,
        currency_key,
        base_currency
    )
);

CREATE TABLE IF NOT EXISTS warehouse.fact_economic_indicator (
    economic_indicator_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    country_key BIGINT NOT NULL
        REFERENCES warehouse.dim_country(country_key),

    indicator_code VARCHAR(50)
        NOT NULL,

    indicator_name VARCHAR(200),

    year_number SMALLINT NOT NULL,

    indicator_value NUMERIC(30,8),

    source VARCHAR(50)
        NOT NULL DEFAULT 'World Bank',

    UNIQUE (
        country_key,
        indicator_code,
        year_number
    )
);

CREATE TABLE IF NOT EXISTS warehouse.fact_weather (
    weather_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    datacenter_key BIGINT NOT NULL
        REFERENCES warehouse.dim_datacenter(datacenter_key),

    date_key INTEGER NOT NULL
        REFERENCES warehouse.dim_date(date_key),

    mean_temperature_c NUMERIC(6,2),

    max_temperature_c NUMERIC(6,2),

    min_temperature_c NUMERIC(6,2),

    precipitation_mm NUMERIC(10,2),

    wind_speed_kmh NUMERIC(10,2),

    source VARCHAR(50)
        NOT NULL DEFAULT 'Open-Meteo',

    UNIQUE (
        datacenter_key,
        date_key
    )
);

CREATE TABLE IF NOT EXISTS ml.customer_churn_prediction (
    prediction_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    customer_key BIGINT NOT NULL
        REFERENCES warehouse.dim_customer(customer_key),

    scoring_date DATE NOT NULL,

    churn_probability NUMERIC(8,6)
        CHECK (
            churn_probability
            BETWEEN 0 AND 1
        ),

    risk_band VARCHAR(20)
        CHECK (
            risk_band IN (
                'Low',
                'Medium',
                'High',
                'Critical'
            )
        ),

    predicted_churn BOOLEAN,

    model_name VARCHAR(100),

    model_version VARCHAR(50),

    top_driver_1 VARCHAR(200),
    top_driver_2 VARCHAR(200),
    top_driver_3 VARCHAR(200),

    created_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        customer_key,
        scoring_date,
        model_version
    )
);

CREATE TABLE IF NOT EXISTS ml.revenue_forecast (
    forecast_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    forecast_created_date DATE NOT NULL,

    forecast_target_date DATE NOT NULL,

    region_key BIGINT
        REFERENCES warehouse.dim_region(region_key),

    product_key BIGINT
        REFERENCES warehouse.dim_product(product_key),

    predicted_revenue_usd NUMERIC(18,2),

    lower_bound_usd NUMERIC(18,2),

    upper_bound_usd NUMERIC(18,2),

    model_name VARCHAR(100),

    model_version VARCHAR(50),

    created_at TIMESTAMPTZ
        DEFAULT CURRENT_TIMESTAMP
);