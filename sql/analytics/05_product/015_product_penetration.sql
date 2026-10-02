-- ============================================================
-- NEXUS 360
-- Q15 - Product Customer Penetration
--
-- Purpose:
--   Measure how deeply each product has penetrated
--   the customer base.
--
-- Skills:
--   COUNT DISTINCT
--   CROSS JOIN
--   penetration %
--   RANK
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_product_penetration AS

WITH total_customers AS (

    SELECT
        COUNT(*) AS customer_count

    FROM warehouse.dim_customer
),

product_usage AS (

    SELECT
        p.product_code,
        p.product_name,
        p.product_family,
        p.service_category,
        p.is_ai_service,

        COUNT(
            DISTINCT f.customer_key
        ) AS customers_using_product,

        SUM(
            f.net_revenue_usd
        ) AS product_revenue_usd

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_product p
        ON p.product_key = f.product_key

    GROUP BY
        p.product_code,
        p.product_name,
        p.product_family,
        p.service_category,
        p.is_ai_service
)

SELECT
    pu.product_code,
    pu.product_name,
    pu.product_family,
    pu.service_category,
    pu.is_ai_service,

    pu.customers_using_product,

    tc.customer_count
        AS total_customer_base,

    ROUND(
        pu.customers_using_product::NUMERIC

        / NULLIF(
            tc.customer_count,
            0
        )

        * 100,
        2
    ) AS customer_penetration_pct,

    ROUND(
        pu.product_revenue_usd,
        2
    ) AS product_revenue_usd,

    RANK() OVER (
        ORDER BY
            pu.customers_using_product DESC
    ) AS penetration_rank

FROM product_usage pu

CROSS JOIN total_customers tc;