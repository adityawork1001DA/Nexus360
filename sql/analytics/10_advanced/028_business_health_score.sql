-- ============================================================
-- NEXUS 360
-- Q28 - Executive Business Health Score
--
-- Purpose:
--   Create a single executive-level health model combining:
--
--      Financial performance
--      Customer retention
--      Customer risk
--      Support quality
--      Platform reliability
--      Sustainability
--
-- Output:
--   Exactly one executive business-health row.
--
-- Consumers:
--   Streamlit
--   Tableau
--   Excel
--   Gemini Executive Copilot
--   Automated reporting
--
-- Demonstrates:
--   cross-domain semantic analytics
--   CROSS JOIN
--   weighted scoring
--   normalization
--   KPI engineering
--   executive decision intelligence
-- ============================================================

DROP VIEW IF EXISTS analytics.v_business_health_score;

CREATE VIEW analytics.v_business_health_score AS

WITH executive AS (

    SELECT
        total_revenue_usd,
        gross_margin_pct,
        sla_compliance_pct,
        request_failure_rate_pct,
        carbon_estimate_kg

    FROM analytics.v_executive_kpis
),

renewal AS (

    SELECT
        COALESCE(
            AVG(renewal_risk_score),
            0
        )::NUMERIC AS avg_renewal_risk_score

    FROM analytics.v_subscription_renewal_risk
),

revenue_risk AS (

    SELECT
        COALESCE(
            SUM(revenue_at_risk_usd),
            0
        )::NUMERIC AS total_revenue_at_risk_usd,

        COALESCE(
            AVG(composite_risk_score),
            0
        )::NUMERIC AS avg_customer_risk_score

    FROM analytics.v_revenue_at_risk
),

sustainability AS (

    SELECT
        COALESCE(
            AVG(renewable_energy_pct),
            0
        )::NUMERIC AS avg_renewable_energy_pct,

        COALESCE(
            AVG(carbon_kg_per_compute_hour),
            0
        )::NUMERIC AS avg_carbon_intensity

    FROM analytics.v_cloud_sustainability
),

components AS (

    SELECT
        e.total_revenue_usd::NUMERIC
            AS total_revenue_usd,

        e.gross_margin_pct::NUMERIC
            AS gross_margin_pct,

        e.sla_compliance_pct::NUMERIC
            AS sla_compliance_pct,

        e.request_failure_rate_pct::NUMERIC
            AS request_failure_rate_pct,

        e.carbon_estimate_kg::NUMERIC
            AS carbon_estimate_kg,

        r.avg_renewal_risk_score,

        rr.total_revenue_at_risk_usd,

        rr.avg_customer_risk_score,

        s.avg_renewable_energy_pct,

        s.avg_carbon_intensity,

        LEAST(
            100::NUMERIC,
            GREATEST(
                0::NUMERIC,
                COALESCE(
                    e.gross_margin_pct::NUMERIC,
                    0::NUMERIC
                )
            )
        ) AS margin_health_score,

        LEAST(
            100::NUMERIC,
            GREATEST(
                0::NUMERIC,
                COALESCE(
                    e.sla_compliance_pct::NUMERIC,
                    0::NUMERIC
                )
            )
        ) AS support_health_score,

        LEAST(
            100::NUMERIC,
            GREATEST(
                0::NUMERIC,

                100::NUMERIC
                -
                (
                    COALESCE(
                        e.request_failure_rate_pct::NUMERIC,
                        0::NUMERIC
                    )
                    * 10::NUMERIC
                )
            )
        ) AS reliability_health_score,

        LEAST(
            100::NUMERIC,
            GREATEST(
                0::NUMERIC,

                100::NUMERIC
                -
                r.avg_renewal_risk_score
            )
        ) AS retention_health_score,

        LEAST(
            100::NUMERIC,
            GREATEST(
                0::NUMERIC,
                s.avg_renewable_energy_pct
            )
        ) AS sustainability_health_score,

        LEAST(
            100::NUMERIC,
            GREATEST(
                0::NUMERIC,

                100::NUMERIC
                -
                rr.avg_customer_risk_score
            )
        ) AS customer_health_score

    FROM executive e

    CROSS JOIN renewal r

    CROSS JOIN revenue_risk rr

    CROSS JOIN sustainability s
),

final_score AS (

    SELECT
        *,

        (
            margin_health_score
            * 0.20::NUMERIC

            +

            support_health_score
            * 0.15::NUMERIC

            +

            reliability_health_score
            * 0.20::NUMERIC

            +

            retention_health_score
            * 0.20::NUMERIC

            +

            sustainability_health_score
            * 0.10::NUMERIC

            +

            customer_health_score
            * 0.15::NUMERIC

        )::NUMERIC AS business_health_score

    FROM components
)

SELECT
    ROUND(
        total_revenue_usd,
        2
    ) AS total_revenue_usd,

    ROUND(
        gross_margin_pct,
        2
    ) AS gross_margin_pct,

    ROUND(
        total_revenue_at_risk_usd,
        2
    ) AS total_revenue_at_risk_usd,

    ROUND(
        avg_renewal_risk_score,
        2
    ) AS avg_renewal_risk_score,

    ROUND(
        sla_compliance_pct,
        2
    ) AS sla_compliance_pct,

    ROUND(
        request_failure_rate_pct,
        4
    ) AS request_failure_rate_pct,

    ROUND(
        avg_renewable_energy_pct,
        2
    ) AS avg_renewable_energy_pct,

    ROUND(
        avg_carbon_intensity,
        6
    ) AS avg_carbon_intensity,

    ROUND(
        margin_health_score,
        2
    ) AS margin_health_score,

    ROUND(
        support_health_score,
        2
    ) AS support_health_score,

    ROUND(
        reliability_health_score,
        2
    ) AS reliability_health_score,

    ROUND(
        retention_health_score,
        2
    ) AS retention_health_score,

    ROUND(
        sustainability_health_score,
        2
    ) AS sustainability_health_score,

    ROUND(
        customer_health_score,
        2
    ) AS customer_health_score,

    ROUND(
        business_health_score,
        2
    ) AS business_health_score,

    CASE
        WHEN business_health_score >= 85
            THEN 'Excellent'

        WHEN business_health_score >= 70
            THEN 'Healthy'

        WHEN business_health_score >= 55
            THEN 'Watch'

        WHEN business_health_score >= 40
            THEN 'At Risk'

        ELSE
            'Critical'
    END AS business_health_band

FROM final_score;