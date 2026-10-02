-- ============================================================
-- NEXUS 360
-- Q07 - Customer Value Tiers
--
-- Skills:
--   aggregation
--   NTILE
--   profitability
--   customer segmentation
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_customer_value_tiers AS

WITH customer_value AS (

    SELECT
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry,
        c.is_ai_customer,

        SUM(
            f.net_revenue_usd
        ) AS lifetime_revenue,

        SUM(
            f.gross_profit_usd
        ) AS lifetime_gross_profit,

        COUNT(
            DISTINCT f.product_key
        ) AS products_purchased,

        COUNT(
            DISTINCT f.transaction_id
        ) AS transaction_count

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_customer c
        ON c.customer_key = f.customer_key

    GROUP BY
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry,
        c.is_ai_customer
),

tiered AS (

    SELECT
        *,

        NTILE(4) OVER (
            ORDER BY lifetime_revenue DESC
        ) AS value_quartile

    FROM customer_value
)

SELECT
    customer_id,
    customer_name,
    customer_segment,
    industry,
    is_ai_customer,

    ROUND(
        lifetime_revenue,
        2
    ) AS lifetime_revenue,

    ROUND(
        lifetime_gross_profit,
        2
    ) AS lifetime_gross_profit,

    ROUND(
        lifetime_gross_profit
        / NULLIF(
            lifetime_revenue,
            0
        )
        * 100,
        2
    ) AS gross_margin_pct,

    products_purchased,
    transaction_count,
    value_quartile,

    CASE value_quartile

        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        ELSE 'Bronze'

    END AS customer_value_tier

FROM tiered;