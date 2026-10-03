-- ============================================================
-- NEXUS 360
-- Q23 - Weather × Cloud Operations Correlation
--
-- Purpose:
--   Examine whether datacenter weather conditions have
--   statistical relationships with cloud workload, cost,
--   reliability, or carbon output.
--
-- Skills:
--   multi-fact join
--   daily aggregation
--   CORR()
--   statistical analytics
-- ============================================================

CREATE OR REPLACE VIEW
analytics.v_weather_cloud_correlation AS

WITH daily_cloud AS (

    SELECT
        u.datacenter_key,
        u.date_key,

        SUM(
            u.compute_hours
        ) AS compute_hours,

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

    GROUP BY
        u.datacenter_key,
        u.date_key
),

combined AS (

    SELECT
        dc.datacenter_code,
        dc.datacenter_name,

        w.mean_temperature_c,
        w.max_temperature_c,
        w.min_temperature_c,
        w.precipitation_mm,
        w.wind_speed_kmh,

        c.compute_hours,
        c.requests_count,
        c.failed_requests,
        c.estimated_cost_usd,
        c.carbon_estimate_kg

    FROM warehouse.fact_weather w

    JOIN daily_cloud c
        ON c.datacenter_key = w.datacenter_key
        AND c.date_key = w.date_key

    JOIN warehouse.dim_datacenter dc
        ON dc.datacenter_key = w.datacenter_key
)

SELECT
    datacenter_code,
    datacenter_name,

    COUNT(*) AS observation_days,

    ROUND(
        CORR(
            mean_temperature_c,
            compute_hours
        )::NUMERIC,
        4
    ) AS temperature_compute_corr,

    ROUND(
        CORR(
            mean_temperature_c,
            estimated_cost_usd
        )::NUMERIC,
        4
    ) AS temperature_cost_corr,

    ROUND(
        CORR(
            mean_temperature_c,
            carbon_estimate_kg
        )::NUMERIC,
        4
    ) AS temperature_carbon_corr,

    ROUND(
        CORR(
            max_temperature_c,
            failed_requests
        )::NUMERIC,
        4
    ) AS max_temperature_failure_corr,

    ROUND(
        CORR(
            precipitation_mm,
            failed_requests
        )::NUMERIC,
        4
    ) AS precipitation_failure_corr,

    ROUND(
        CORR(
            wind_speed_kmh,
            failed_requests
        )::NUMERIC,
        4
    ) AS wind_failure_corr

FROM combined

GROUP BY
    datacenter_code,
    datacenter_name;