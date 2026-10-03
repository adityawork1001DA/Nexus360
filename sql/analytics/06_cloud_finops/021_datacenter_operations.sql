-- ============================================================
-- NEXUS 360
-- Q21 - Datacenter Operational Intelligence
--
-- Purpose:
--   Analyze workload, reliability, cost and sustainability
--   across datacenters.
--
-- Note:
--   capacity_mw and compute_hours are different physical
--   measures. No unsupported utilization % is calculated.
--
-- Skills:
--   dimensional joins
--   aggregation
--   RANK
--   operational intensity metrics
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_datacenter_operations AS

WITH dc_usage AS (

    SELECT
        dc.datacenter_key,
        dc.datacenter_code,
        dc.datacenter_name,
        dc.city,
        dc.capacity_mw,
        dc.renewable_energy_pct,
        dc.operational_since,

        co.country_code,
        co.country_name,

        r.region_code,
        r.region_name,

        COUNT(
            DISTINCT u.customer_key
        ) AS customers,

        COUNT(
            DISTINCT u.product_key
        ) AS products,

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

    FROM warehouse.dim_datacenter dc

    LEFT JOIN warehouse.dim_country co
        ON co.country_key = dc.country_key

    LEFT JOIN warehouse.dim_region r
        ON r.region_key = dc.region_key

    LEFT JOIN warehouse.fact_cloud_usage u
        ON u.datacenter_key = dc.datacenter_key

    GROUP BY
        dc.datacenter_key,
        dc.datacenter_code,
        dc.datacenter_name,
        dc.city,
        dc.capacity_mw,
        dc.renewable_energy_pct,
        dc.operational_since,
        co.country_code,
        co.country_name,
        r.region_code,
        r.region_name
)

SELECT
    datacenter_code,
    datacenter_name,
    city,
    country_code,
    country_name,
    region_code,
    region_name,

    capacity_mw,
    renewable_energy_pct,
    operational_since,

    customers,
    products,

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
        compute_hours
        / NULLIF(capacity_mw, 0),
        2
    ) AS compute_hours_per_capacity_mw,

    ROUND(
        requests_count::NUMERIC
        / NULLIF(capacity_mw, 0),
        2
    ) AS requests_per_capacity_mw,

    ROUND(
        failed_requests::NUMERIC
        / NULLIF(requests_count, 0)
        * 100,
        4
    ) AS request_failure_rate_pct,

    ROUND(
        estimated_cost_usd
        / NULLIF(compute_hours, 0),
        4
    ) AS cost_per_compute_hour_usd,

    RANK() OVER (
        ORDER BY compute_hours DESC
    ) AS workload_rank,

    RANK() OVER (
        ORDER BY carbon_estimate_kg ASC
    ) AS carbon_efficiency_rank

FROM dc_usage;