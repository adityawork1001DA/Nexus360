CREATE OR REPLACE VIEW
analytics.vw_monthly_revenue AS

SELECT
    d.year_number,
    d.month_number,
    d.year_month,

    r.region_name,

    p.product_family,
    p.product_name,

    c.customer_segment,

    SUM(f.net_revenue_usd)
        AS net_revenue_usd,

    SUM(f.gross_profit_usd)
        AS gross_profit_usd,

    COUNT(DISTINCT f.customer_key)
        AS active_customers,

    COUNT(DISTINCT f.transaction_id)
        AS transaction_count

FROM warehouse.fact_revenue f

JOIN warehouse.dim_date d
    ON f.date_key = d.date_key

JOIN warehouse.dim_region r
    ON f.region_key = r.region_key

JOIN warehouse.dim_product p
    ON f.product_key = p.product_key

JOIN warehouse.dim_customer c
    ON f.customer_key = c.customer_key

GROUP BY
    d.year_number,
    d.month_number,
    d.year_month,
    r.region_name,
    p.product_family,
    p.product_name,
    c.customer_segment;

CREATE OR REPLACE VIEW
analytics.vw_customer_360 AS

SELECT
    c.customer_key,
    c.customer_id,
    c.customer_name,
    c.industry,
    c.customer_segment,
    c.customer_status,
    c.is_ai_customer,

    COALESCE(
        SUM(r.net_revenue_usd),
        0
    ) AS lifetime_revenue_usd,

    COALESCE(
        SUM(r.gross_profit_usd),
        0
    ) AS lifetime_gross_profit_usd,

    COUNT(
        DISTINCT r.product_key
    ) AS products_purchased,

    MIN(d.full_date)
        AS first_revenue_date,

    MAX(d.full_date)
        AS latest_revenue_date

FROM warehouse.dim_customer c

LEFT JOIN warehouse.fact_revenue r
    ON c.customer_key = r.customer_key

LEFT JOIN warehouse.dim_date d
    ON r.date_key = d.date_key

GROUP BY
    c.customer_key,
    c.customer_id,
    c.customer_name,
    c.industry,
    c.customer_segment,
    c.customer_status,
    c.is_ai_customer;
