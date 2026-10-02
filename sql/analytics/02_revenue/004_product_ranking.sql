-- ============================================================
-- Q04 - Product Revenue Ranking
--
-- Skills:
--   aggregation
--   RANK
--   percent-of-total
--   window aggregation
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_product_revenue_rank AS

WITH product_revenue AS (

    SELECT
        p.product_key,
        p.product_code,
        p.product_name,
        p.product_family,

        SUM(
            f.net_revenue_usd
        ) AS revenue_usd,

        COUNT(
            DISTINCT f.customer_key
        ) AS customers,

        COUNT(*) AS transactions

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_product p
        ON p.product_key =
           f.product_key

    GROUP BY
        p.product_key,
        p.product_code,
        p.product_name,
        p.product_family
)

SELECT
    product_code,
    product_name,
    product_family,

    ROUND(
        revenue_usd,
        2
    ) AS revenue_usd,

    customers,
    transactions,

    RANK() OVER (
        ORDER BY revenue_usd DESC
    ) AS revenue_rank,

    ROUND(
        revenue_usd
        / NULLIF(
            SUM(
                revenue_usd
            ) OVER (),
            0
        )
        * 100,
        2
    ) AS revenue_share_pct

FROM product_revenue;