CREATE TABLE IF NOT EXISTS staging.customers (
    LIKE raw.customers
    INCLUDING DEFAULTS
);


CREATE TABLE IF NOT EXISTS staging.subscriptions (
    LIKE raw.subscriptions
    INCLUDING DEFAULTS
);


CREATE TABLE IF NOT EXISTS staging.revenue (
    LIKE raw.revenue
    INCLUDING DEFAULTS
);


CREATE TABLE IF NOT EXISTS staging.cloud_usage (
    LIKE raw.cloud_usage
    INCLUDING DEFAULTS
);


CREATE TABLE IF NOT EXISTS staging.support_tickets (
    LIKE raw.support_tickets
    INCLUDING DEFAULTS
);