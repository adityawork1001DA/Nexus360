CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,

    day_of_month SMALLINT NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    day_of_week SMALLINT NOT NULL,

    week_of_year SMALLINT NOT NULL,

    month_number SMALLINT NOT NULL,
    month_name VARCHAR(10) NOT NULL,

    quarter_number SMALLINT NOT NULL,

    year_number SMALLINT NOT NULL,

    year_month VARCHAR(7) NOT NULL,

    is_weekend BOOLEAN NOT NULL,

    fiscal_year SMALLINT,
    fiscal_quarter SMALLINT
);

-----------------------------------------------------

CREATE TABLE IF NOT EXISTS warehouse.dim_country (
    country_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    country_code CHAR(3) NOT NULL UNIQUE,

    country_name VARCHAR(100) NOT NULL,

    world_bank_code CHAR(3),

    continent VARCHAR(50),

    income_group VARCHAR(100),

    currency_code CHAR(3),

    active_flag BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-----------------------------------------------------

CREATE TABLE IF NOT EXISTS warehouse.dim_region (
    region_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    region_code VARCHAR(20) NOT NULL UNIQUE,

    region_name VARCHAR(100) NOT NULL,

    geography_group VARCHAR(50),

    active_flag BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


---------------------------------------------

CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    customer_id VARCHAR(30) NOT NULL UNIQUE,

    customer_name VARCHAR(200) NOT NULL,

    industry VARCHAR(100),

    customer_segment VARCHAR(30)
        CHECK (
            customer_segment IN (
                'SMB',
                'Mid-Market',
                'Enterprise',
                'Strategic'
            )
        ),

    country_key BIGINT
        REFERENCES warehouse.dim_country(country_key),

    region_key BIGINT
        REFERENCES warehouse.dim_region(region_key),

    employee_band VARCHAR(50),

    annual_revenue_band VARCHAR(50),

    acquisition_channel VARCHAR(100),

    signup_date DATE NOT NULL,

    customer_status VARCHAR(30) NOT NULL
        CHECK (
            customer_status IN (
                'Active',
                'At Risk',
                'Churned',
                'Suspended'
            )
        ),

    is_ai_customer BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


--------------------------------------------------

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    product_code VARCHAR(30) NOT NULL UNIQUE,

    product_name VARCHAR(150) NOT NULL,

    product_family VARCHAR(100) NOT NULL,

    service_category VARCHAR(100),

    pricing_model VARCHAR(50),

    unit_of_measure VARCHAR(50),

    is_ai_service BOOLEAN NOT NULL DEFAULT FALSE,

    active_flag BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-------------------------------------------------

CREATE TABLE IF NOT EXISTS warehouse.dim_datacenter (
    datacenter_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    datacenter_code VARCHAR(30) NOT NULL UNIQUE,

    datacenter_name VARCHAR(150) NOT NULL,

    city VARCHAR(100),

    country_key BIGINT
        REFERENCES warehouse.dim_country(country_key),

    region_key BIGINT
        REFERENCES warehouse.dim_region(region_key),

    latitude NUMERIC(9,6),

    longitude NUMERIC(9,6),

    capacity_mw NUMERIC(12,2)
        CHECK (capacity_mw >= 0),

    renewable_energy_pct NUMERIC(5,2)
        CHECK (
            renewable_energy_pct
            BETWEEN 0 AND 100
        ),

    operational_since DATE,

    active_flag BOOLEAN NOT NULL DEFAULT TRUE
);


------------------------------------------------

CREATE TABLE IF NOT EXISTS warehouse.dim_currency (
    currency_key BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    currency_code CHAR(3) NOT NULL UNIQUE,

    currency_name VARCHAR(100),

    currency_symbol VARCHAR(10),

    active_flag BOOLEAN NOT NULL DEFAULT TRUE
);