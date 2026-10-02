-- ============================================================
-- NEXUS 360
-- Q17 - Support SLA Performance
--
-- Purpose:
--   Analyze support quality across severity levels.
--
-- Skills:
--   FILTER
--   AVG
--   conditional aggregation
--   ranking
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_support_sla_performance AS

WITH performance AS (

    SELECT
        severity,

        COUNT(*) AS total_tickets,

        COUNT(*) FILTER (
            WHERE sla_met = TRUE
        ) AS sla_met_tickets,

        COUNT(*) FILTER (
            WHERE sla_met = FALSE
        ) AS sla_breached_tickets,

        COUNT(*) FILTER (
            WHERE reopened = TRUE
        ) AS reopened_tickets,

        AVG(
            resolution_hours
        ) AS avg_resolution_hours,

        AVG(
            sla_target_hours
        ) AS avg_sla_target_hours,

        AVG(
            customer_satisfaction
        ) AS avg_customer_satisfaction

    FROM warehouse.fact_support_ticket

    GROUP BY severity
)

SELECT
    severity,
    total_tickets,
    sla_met_tickets,
    sla_breached_tickets,
    reopened_tickets,

    ROUND(
        sla_met_tickets::NUMERIC

        / NULLIF(
            total_tickets,
            0
        )

        * 100,
        2
    ) AS sla_compliance_pct,

    ROUND(
        reopened_tickets::NUMERIC

        / NULLIF(
            total_tickets,
            0
        )

        * 100,
        2
    ) AS reopen_rate_pct,

    ROUND(
        avg_resolution_hours,
        2
    ) AS avg_resolution_hours,

    ROUND(
        avg_sla_target_hours,
        2
    ) AS avg_sla_target_hours,

    ROUND(
        avg_customer_satisfaction,
        2
    ) AS avg_customer_satisfaction,

    RANK() OVER (
        ORDER BY
            (
                sla_met_tickets::NUMERIC
                / NULLIF(
                    total_tickets,
                    0
                )
            ) DESC
    ) AS sla_performance_rank

FROM performance;