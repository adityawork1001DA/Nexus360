-- ============================================================
-- NEXUS 360
-- Q20 - Customer Cloud Efficiency
--
-- Purpose:
--   Compare customer revenue against cloud operating cost and
--   consumption to identify efficient and expensive accounts.
--
-- Skills:
--   multiple CTEs
--   LEFT JOIN
--   COALESCE
--   unit economics
--   NTILE
-- ============================================================

CREATE OR REPLACE VIEW
analytics.v_customer_cloud_efficiency AS

WITH revenue AS (

    SELECT
        customer_key,

        SUM(
            net_revenue_usd
        ) AS revenue_usd,

        SUM(
            gross_profit_usd
        ) AS gross_profit_usd

    FROM warehouse.fact_revenue

    GROUP BY customer_key
),

cloud AS (

    SELECT
        customer_key,

        SUM(
            compute_hours
        ) AS compute_hours,

        SUM(
            ai_tokens_million
        ) AS ai_tokens_million,

        SUM(
            requests_count
        ) AS requests_count,

        SUM(
            failed_requests
        ) AS failed_requests,

        SUM(
            estimated_cost_usd
        ) AS cloud_cost_usd,

        SUM(
            carbon_estimate_kg
        ) AS carbon_estimate_kg

    FROM warehouse.fact_cloud_usage

    GROUP BY customer_key
),

base AS (

    SELECT
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry,
        c.is_ai_customer,

        COALESCE(
            r.revenue_usd,
            0
        ) AS revenue_usd,

        COALESCE(
            r.gross_profit_usd,
            0
        ) AS gross_profit_usd,

        COALESCE(
            cl.compute_hours,
            0
        ) AS compute_hours,

        COALESCE(
            cl.ai_tokens_million,
            0
        ) AS ai_tokens_million,

        COALESCE(
            cl.requests_count,
            0
        ) AS requests_count,

        COALESCE(
            cl.failed_requests,
            0
        ) AS failed_requests,

        COALESCE(
            cl.cloud_cost_usd,
            0
        ) AS cloud_cost_usd,

        COALESCE(
            cl.carbon_estimate_kg,
            0
        ) AS carbon_estimate_kg

    FROM warehouse.dim_customer c

    LEFT JOIN revenue r
        ON r.customer_key = c.customer_key

    LEFT JOIN cloud cl
        ON cl.customer_key = c.customer_key
),

scored AS (

    SELECT
        *,

        NTILE(5) OVER (
            ORDER BY
                (
                    revenue_usd
                    / NULLIF(cloud_cost_usd, 0)
                )
        ) AS efficiency_quintile

    FROM base
)

SELECT
    customer_id,
    customer_name,
    customer_segment,
    industry,
    is_ai_customer,

    ROUND(
        revenue_usd,
        2
    ) AS revenue_usd,

    ROUND(
        gross_profit_usd,
        2
    ) AS gross_profit_usd,

    ROUND(
        cloud_cost_usd,
        2
    ) AS cloud_cost_usd,

    ROUND(
        compute_hours,
        2
    ) AS compute_hours,

    ROUND(
        ai_tokens_million,
        2
    ) AS ai_tokens_million,

    requests_count,
    failed_requests,

    ROUND(
        revenue_usd
        / NULLIF(cloud_cost_usd, 0),
        4
    ) AS revenue_to_cloud_cost_ratio,

    ROUND(
        cloud_cost_usd
        / NULLIF(revenue_usd, 0)
        * 100,
        2
    ) AS cloud_cost_to_revenue_pct,

    ROUND(
        failed_requests::NUMERIC
        / NULLIF(requests_count, 0)
        * 100,
        4
    ) AS request_failure_rate_pct,

    ROUND(
        carbon_estimate_kg,
        2
    ) AS carbon_estimate_kg,

    efficiency_quintile,

    CASE
        WHEN efficiency_quintile = 5
            THEN 'Highly Efficient'

        WHEN efficiency_quintile = 4
            THEN 'Efficient'

        WHEN efficiency_quintile = 3
            THEN 'Average'

        WHEN efficiency_quintile = 2
            THEN 'Cost Heavy'

        ELSE 'Optimization Priority'
    END AS cloud_efficiency_band

FROM scored;