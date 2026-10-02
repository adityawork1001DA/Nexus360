INSERT INTO warehouse.fact_revenue (
    transaction_id,
    date_key,
    customer_key,
    product_key,
    region_key,
    currency_key,
    quantity,
    gross_revenue_local,
    discount_local,
    net_revenue_local,
    fx_rate_to_usd,
    net_revenue_usd,
    estimated_cost_usd,
    gross_profit_usd,
    revenue_type
)

SELECT
    s.transaction_id,

    TO_CHAR(
        s.transaction_date,
        'YYYYMMDD'
    )::INTEGER,

    c.customer_key,
    p.product_key,
    r.region_key,
    cur.currency_key,

    s.quantity,
    s.gross_revenue_local,
    s.discount_local,
    s.net_revenue_local,
    s.fx_rate_to_usd,
    s.net_revenue_usd,
    s.estimated_cost_usd,
    s.gross_profit_usd,
    s.revenue_type

FROM staging.revenue s

JOIN warehouse.dim_customer c
    ON c.customer_id =
       s.customer_id

JOIN warehouse.dim_product p
    ON p.product_code =
       s.product_code

JOIN warehouse.dim_region r
    ON r.region_code =
       s.region_code

JOIN warehouse.dim_currency cur
    ON cur.currency_code =
       s.currency_code

ON CONFLICT (transaction_id)

DO UPDATE SET
    net_revenue_usd =
        EXCLUDED.net_revenue_usd,

    estimated_cost_usd =
        EXCLUDED.estimated_cost_usd,

    gross_profit_usd =
        EXCLUDED.gross_profit_usd;