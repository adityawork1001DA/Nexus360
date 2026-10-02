INSERT INTO warehouse.fact_subscription (
    subscription_id,
    customer_key,
    product_key,
    start_date_key,
    end_date_key,
    billing_frequency,
    contract_value_usd,
    seats,
    subscription_status,
    auto_renew
)

SELECT
    s.subscription_id,
    c.customer_key,
    p.product_key,

    TO_CHAR(
        s.start_date,
        'YYYYMMDD'
    )::INTEGER,

    CASE
        WHEN s.end_date IS NULL
        THEN NULL

        ELSE TO_CHAR(
            s.end_date,
            'YYYYMMDD'
        )::INTEGER
    END,

    s.billing_frequency,
    s.contract_value_usd,
    s.seats,
    s.subscription_status,
    s.auto_renew

FROM staging.subscriptions s

JOIN warehouse.dim_customer c
    ON c.customer_id =
       s.customer_id

JOIN warehouse.dim_product p
    ON p.product_code =
       s.product_code

ON CONFLICT (subscription_id)

DO UPDATE SET
    contract_value_usd =
        EXCLUDED.contract_value_usd,

    seats =
        EXCLUDED.seats,

    subscription_status =
        EXCLUDED.subscription_status,

    auto_renew =
        EXCLUDED.auto_renew;