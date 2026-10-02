CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id VARCHAR(30) PRIMARY KEY,
    customer_name VARCHAR(200),
    industry VARCHAR(100),
    customer_segment VARCHAR(30),
    country_code CHAR(3),
    region_code VARCHAR(20),
    employee_band VARCHAR(50),
    annual_revenue_band VARCHAR(50),
    acquisition_channel VARCHAR(100),
    signup_date DATE,
    customer_status VARCHAR(30),
    is_ai_customer BOOLEAN,

    _source_system VARCHAR(50) DEFAULT 'synthetic_crm',
    _source_file VARCHAR(255),
    _ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    _run_id BIGINT,
    _record_hash VARCHAR(64)
);


CREATE TABLE IF NOT EXISTS raw.subscriptions (
    subscription_id VARCHAR(40) PRIMARY KEY,
    customer_id VARCHAR(30),
    product_code VARCHAR(30),
    start_date DATE,
    end_date DATE,
    billing_frequency VARCHAR(20),
    contract_value_usd NUMERIC(18,2),
    seats INTEGER,
    subscription_status VARCHAR(20),
    auto_renew BOOLEAN,

    _source_system VARCHAR(50) DEFAULT 'synthetic_billing',
    _source_file VARCHAR(255),
    _ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    _run_id BIGINT,
    _record_hash VARCHAR(64)
);


CREATE TABLE IF NOT EXISTS raw.revenue (
    transaction_id VARCHAR(50) PRIMARY KEY,
    transaction_date DATE,
    customer_id VARCHAR(30),
    product_code VARCHAR(30),
    region_code VARCHAR(20),
    currency_code CHAR(3),

    quantity NUMERIC(18,4),
    gross_revenue_local NUMERIC(18,2),
    discount_local NUMERIC(18,2),
    net_revenue_local NUMERIC(18,2),
    fx_rate_to_usd NUMERIC(18,8),
    net_revenue_usd NUMERIC(18,2),
    estimated_cost_usd NUMERIC(18,2),
    gross_profit_usd NUMERIC(18,2),
    revenue_type VARCHAR(30),

    _source_system VARCHAR(50) DEFAULT 'synthetic_billing',
    _source_file VARCHAR(255),
    _ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    _run_id BIGINT,
    _record_hash VARCHAR(64)
);


CREATE TABLE IF NOT EXISTS raw.cloud_usage (
    usage_id VARCHAR(50) PRIMARY KEY,
    usage_date DATE,
    customer_id VARCHAR(30),
    product_code VARCHAR(30),
    region_code VARCHAR(20),
    datacenter_code VARCHAR(30),

    compute_hours NUMERIC(18,4),
    storage_gb NUMERIC(18,4),
    network_gb NUMERIC(18,4),
    ai_tokens_million NUMERIC(18,4),
    requests_count BIGINT,
    failed_requests BIGINT,
    estimated_cost_usd NUMERIC(18,2),
    carbon_estimate_kg NUMERIC(18,4),

    _source_system VARCHAR(50) DEFAULT 'synthetic_telemetry',
    _source_file VARCHAR(255),
    _ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    _run_id BIGINT,
    _record_hash VARCHAR(64)
);


CREATE TABLE IF NOT EXISTS raw.support_tickets (
    ticket_id VARCHAR(40) PRIMARY KEY,
    customer_id VARCHAR(30),
    product_code VARCHAR(30),
    opened_date DATE,
    closed_date DATE,

    severity VARCHAR(10),
    category VARCHAR(100),

    resolution_hours NUMERIC(12,2),
    sla_target_hours NUMERIC(12,2),
    sla_met BOOLEAN,
    reopened BOOLEAN,
    customer_satisfaction NUMERIC(3,2),

    _source_system VARCHAR(50) DEFAULT 'synthetic_support',
    _source_file VARCHAR(255),
    _ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    _run_id BIGINT,
    _record_hash VARCHAR(64)
);