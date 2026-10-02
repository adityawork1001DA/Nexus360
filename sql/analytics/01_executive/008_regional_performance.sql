-- ============================================================
-- NEXUS 360
-- Q08 - Regional Revenue Performance
--
-- Skills:
--   dimensional joins
--   ranking
--   revenue share
--   profitability
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_regional_performance AS

WITH regional AS (

    SELECT
        r.region_key,
        r.region_code,
        r.region_name,
        r.geography_group,

        SUM(
            f.net_revenue_usd
        ) AS revenue_usd,

        SUM(
            f.gross_profit_usd
        ) AS gross_profit_usd,

        SUM(
            f.estimated_cost_usd
        ) AS estimated_cost_usd,

        COUNT(
            DISTINCT f.customer_key
        ) AS customers,

        COUNT(
            DISTINCT f.product_key
        ) AS products,

        COUNT(
            DISTINCT f.transaction_id
        ) AS transactions

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_region r
        ON r.region_key = f.region_key

    GROUP BY
        r.region_key,
        r.region_code,
        r.region_name,
        r.geography_group
)

SELECT
    region_code,
    region_name,
    geography_group,

    ROUND(
        revenue_usd,
        2
    ) AS revenue_usd,

    ROUND(
        gross_profit_usd,
        2
    ) AS gross_profit_usd,

    ROUND(
        estimated_cost_usd,
        2
    ) AS estimated_cost_usd,

    customers,
    products,
    transactions,

    RANK() OVER (
        ORDER BY revenue_usd DESC
    ) AS regional_rank,

    ROUND(
        revenue_usd
        / NULLIF(
            SUM(revenue_usd) OVER (),
            0
        )
        * 100,
        2
    ) AS global_revenue_share_pct,

    ROUND(
        revenue_usd
        / NULLIF(customers, 0),
        2
    ) AS revenue_per_customer,

    ROUND(
        gross_profit_usd
        / NULLIF(revenue_usd, 0)
        * 100,
        2
    ) AS gross_margin_pct

FROM regional;