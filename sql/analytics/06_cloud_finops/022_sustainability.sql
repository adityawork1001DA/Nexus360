-- ============================================================
-- NEXUS 360
-- Q22 - Cloud Sustainability Intelligence
--
-- Purpose:
--   Analyze datacenter sustainability, carbon intensity,
--   renewable-energy adoption, workload, cost and reliability.
--
-- Architecture:
--   This view is consumed by downstream semantic assets,
--   including analytics.v_business_health_score.
--
--   Therefore this file intentionally uses CREATE OR REPLACE
--   VIEW rather than DROP VIEW.
--
-- IMPORTANT:
--   Do not reorder, rename or change the datatype of existing
--   output columns without an explicit migration.
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_cloud_sustainability AS

WITH datacenter_sustainability AS (

    SELECT
        dc.datacenter_key,
        dc.datacenter_code,
        dc.datacenter_name,
        dc.city,

        CAST(
            COALESCE(
                co.country_code,
                'UNK'
            )
            AS CHARACTER(3)
        ) AS country_code,

        CAST(
            COALESCE(
                co.country_name,
                'Unknown'
            )
            AS VARCHAR(100)
        ) AS country_name,

        dc.capacity_mw,
        dc.renewable_energy_pct,

        COUNT(
            DISTINCT u.customer_key
        ) AS active_customers,

        COUNT(
            DISTINCT u.product_key
        ) AS active_products,

        COALESCE(
            SUM(u.compute_hours),
            0
        ) AS compute_hours,

        COALESCE(
            SUM(u.storage_gb),
            0
        ) AS storage_gb,

        COALESCE(
            SUM(u.network_gb),
            0
        ) AS network_gb,

        COALESCE(
            SUM(u.ai_tokens_million),
            0
        ) AS ai_tokens_million,

        COALESCE(
            SUM(u.requests_count),
            0
        ) AS requests_count,

        COALESCE(
            SUM(u.failed_requests),
            0
        ) AS failed_requests,

        COALESCE(
            SUM(u.estimated_cost_usd),
            0
        ) AS estimated_cost_usd,

        COALESCE(
            SUM(u.carbon_estimate_kg),
            0
        ) AS carbon_estimate_kg

    FROM warehouse.dim_datacenter dc

    LEFT JOIN warehouse.dim_country co
        ON co.country_key = dc.country_key

    LEFT JOIN warehouse.fact_cloud_usage u
        ON u.datacenter_key = dc.datacenter_key

    WHERE dc.active_flag = TRUE

    GROUP BY
        dc.datacenter_key,
        dc.datacenter_code,
        dc.datacenter_name,
        dc.city,
        co.country_code,
        co.country_name,
        dc.capacity_mw,
        dc.renewable_energy_pct
),

calculated AS (

    SELECT
        datacenter_key,
        datacenter_code,
        datacenter_name,
        city,
        country_code,
        country_name,
        capacity_mw,
        renewable_energy_pct,
        active_customers,
        active_products,
        compute_hours,
        storage_gb,
        network_gb,
        ai_tokens_million,
        requests_count,
        failed_requests,
        estimated_cost_usd,
        carbon_estimate_kg,

        carbon_estimate_kg
        / NULLIF(
            compute_hours,
            0
        ) AS carbon_kg_per_compute_hour,

        carbon_estimate_kg
        / NULLIF(
            requests_count,
            0
        )
        * 1000000
            AS carbon_kg_per_million_requests,

        estimated_cost_usd
        / NULLIF(
            compute_hours,
            0
        ) AS cost_per_compute_hour_usd,

        failed_requests::NUMERIC
        / NULLIF(
            requests_count,
            0
        )
        * 100
            AS request_failure_rate_pct

    FROM datacenter_sustainability
),

classified AS (

    SELECT
        *,

        CASE
            WHEN renewable_energy_pct >= 80
                THEN 'Renewable Leader'

            WHEN renewable_energy_pct >= 60
                THEN 'Strong Renewable Mix'

            WHEN renewable_energy_pct >= 40
                THEN 'Transitioning'

            ELSE
                'Renewable Improvement Priority'
        END AS renewable_energy_band

    FROM calculated
)

SELECT
    datacenter_code,
    datacenter_name,
    city,

    country_code,
    country_name,

    capacity_mw,
    renewable_energy_pct,

    active_customers,
    active_products,

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
        carbon_kg_per_compute_hour,
        6
    ) AS carbon_kg_per_compute_hour,

    ROUND(
        carbon_kg_per_million_requests,
        6
    ) AS carbon_kg_per_million_requests,

    ROUND(
        cost_per_compute_hour_usd,
        4
    ) AS cost_per_compute_hour_usd,

    ROUND(
        request_failure_rate_pct,
        4
    ) AS request_failure_rate_pct,

    renewable_energy_band,

    RANK() OVER (
        ORDER BY
            carbon_kg_per_compute_hour ASC NULLS LAST
    ) AS carbon_intensity_rank,

    RANK() OVER (
        ORDER BY
            renewable_energy_pct DESC NULLS LAST
    ) AS renewable_energy_rank,

    RANK() OVER (
        ORDER BY
            compute_hours DESC NULLS LAST
    ) AS workload_rank

FROM classified;