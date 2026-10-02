-- ============================================================
-- NEXUS 360
-- Q18 - Support Resolution Percentiles
--
-- Purpose:
--   Measure P50 / P75 / P90 / P95 resolution times.
--
-- Why:
--   Averages alone hide long-tail support incidents.
--
-- Skills:
--   PERCENTILE_CONT
--   ordered-set aggregates
--   statistical analysis
-- ============================================================

CREATE OR REPLACE VIEW
analytics.v_support_resolution_percentiles AS

SELECT
    severity,

    COUNT(*) AS total_tickets,

    ROUND(
        AVG(
            resolution_hours
        ),
        2
    ) AS avg_resolution_hours,

    ROUND(
        PERCENTILE_CONT(0.50)
        WITHIN GROUP (
            ORDER BY resolution_hours
        )::NUMERIC,
        2
    ) AS p50_resolution_hours,

    ROUND(
        PERCENTILE_CONT(0.75)
        WITHIN GROUP (
            ORDER BY resolution_hours
        )::NUMERIC,
        2
    ) AS p75_resolution_hours,

    ROUND(
        PERCENTILE_CONT(0.90)
        WITHIN GROUP (
            ORDER BY resolution_hours
        )::NUMERIC,
        2
    ) AS p90_resolution_hours,

    ROUND(
        PERCENTILE_CONT(0.95)
        WITHIN GROUP (
            ORDER BY resolution_hours
        )::NUMERIC,
        2
    ) AS p95_resolution_hours,

    ROUND(
        AVG(
            customer_satisfaction
        ),
        2
    ) AS avg_customer_satisfaction

FROM warehouse.fact_support_ticket

WHERE resolution_hours IS NOT NULL

GROUP BY severity;