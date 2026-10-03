-- ============================================================
-- NEXUS 360
-- Q19 - Cloud FinOps Unit Economics
--
-- Purpose:
--   Measure cloud consumption, reliability, cost efficiency,
--   and carbon intensity by product.
--
-- Skills:
--   CTE
--   dimensional aggregation
--   conditional metrics
--   safe division
--   window ranking
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_cloud_finops AS

WITH product_usage AS (

    SELECT
        p.product_key,
        p.product_code,
        p.product_name,
        p.product_family,
        p.service_category,
        p.is_ai_service,

        COUNT(
            DISTINCT u.customer_key
        ) AS active_customers,

        SUM(
            u.compute_hours
        ) AS compute_hours,

        SUM(
            u.storage_gb
        ) AS storage_gb,

        SUM(
            u.network_gb
        ) AS network_gb,

        SUM(
            u.ai_tokens_million
        ) AS ai_tokens_million,

        SUM(
            u.requests_count
        ) AS requests_count,

        SUM(
            u.failed_requests
        ) AS failed_requests,

        SUM(
            u.estimated_cost_usd
        ) AS estimated_cost_usd,

        SUM(
            u.carbon_estimate_kg
        ) AS carbon_estimate_kg

    FROM warehouse.fact_cloud_usage u

    JOIN warehouse.dim_product p
        ON p.product_key = u.product_key

    GROUP BY
        p.product_key,
        p.product_code,
        p.product_name,
        p.product_family,
        p.service_category,
        p.is_ai_service
)

SELECT
    product_code,
    product_name,
    product_family,
    service_category,
    is_ai_service,
    active_customers,

    ROUND(
        compute_hours,
        2
    ) AS compute_hours,

    ROUND(
        storage_gb,
        2
    ) AS storage_gb,

    ROUND(
        network_gb,
        2
    ) AS network_gb,

    ROUND(
        ai_tokens_million,
        2
    ) AS ai_tokens_million,

    requests_count,
    failed_requests,

    ROUND(
        estimated_cost_usd,
        2
    ) AS estimated_cost_usd,

    ROUND(
        carbon_estimate_kg,
        2
    ) AS carbon_estimate_kg,

    ROUND(
        estimated_cost_usd
        / NULLIF(compute_hours, 0),
        4
    ) AS cost_per_compute_hour_usd,

    ROUND(
        estimated_cost_usd
        / NULLIF(requests_count, 0)
        * 1000000,
        4
    ) AS cost_per_million_requests_usd,

    ROUND(
        failed_requests::NUMERIC
        / NULLIF(requests_count, 0)
        * 100,
        4
    ) AS request_failure_rate_pct,

    ROUND(
        carbon_estimate_kg
        / NULLIF(compute_hours, 0),
        6
    ) AS carbon_kg_per_compute_hour,

    RANK() OVER (
        ORDER BY estimated_cost_usd DESC
    ) AS cloud_cost_rank

FROM product_usage;