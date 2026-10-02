TRUNCATE TABLE
    staging.support_tickets,
    staging.cloud_usage,
    staging.revenue,
    staging.subscriptions,
    staging.customers;


INSERT INTO staging.customers
SELECT *
FROM raw.customers
WHERE
    customer_id IS NOT NULL
    AND customer_name IS NOT NULL
    AND customer_segment IN (
        'SMB',
        'Mid-Market',
        'Enterprise',
        'Strategic'
    );


INSERT INTO staging.subscriptions
SELECT *
FROM raw.subscriptions
WHERE
    subscription_id IS NOT NULL
    AND customer_id IS NOT NULL
    AND product_code IS NOT NULL
    AND contract_value_usd >= 0;


INSERT INTO staging.revenue
SELECT *
FROM raw.revenue
WHERE
    transaction_id IS NOT NULL
    AND transaction_date IS NOT NULL
    AND customer_id IS NOT NULL
    AND net_revenue_usd >= 0;


INSERT INTO staging.cloud_usage
SELECT *
FROM raw.cloud_usage
WHERE
    usage_id IS NOT NULL
    AND usage_date IS NOT NULL
    AND customer_id IS NOT NULL
    AND compute_hours >= 0
    AND storage_gb >= 0
    AND network_gb >= 0;


INSERT INTO staging.support_tickets
SELECT *
FROM raw.support_tickets
WHERE
    ticket_id IS NOT NULL
    AND customer_id IS NOT NULL
    AND severity IN (
        'SEV1',
        'SEV2',
        'SEV3',
        'SEV4'
    );