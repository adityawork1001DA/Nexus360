-- ============================================================
-- NEXUS 360
-- Q27 - Revenue at Risk Intelligence
--
-- Purpose:
--   Estimate customer-level commercial revenue exposure by
--   combining:
--
--      Revenue
--      Subscription renewal risk
--      Support SLA performance
--      Ticket reopening behaviour
--      Cloud reliability
--
-- Grain:
--   One row per customer.
--
-- Downstream dependency:
--   analytics.v_business_health_score
--
-- IMPORTANT:
--   Do NOT DROP this view during normal analytics builds.
--   CREATE OR REPLACE preserves downstream dependencies.
--
--   Existing output column names, order and datatypes must
--   remain stable unless an explicit migration is performed.
-- ============================================================


CREATE OR REPLACE VIEW analytics.v_revenue_at_risk AS

WITH customer_base AS (

    SELECT
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry,
        c.customer_status,
        c.is_ai_customer,

        COALESCE(
            SUM(r.net_revenue_usd),
            0
        ) AS lifetime_revenue_usd

    FROM warehouse.dim_customer c

    LEFT JOIN warehouse.fact_revenue r
        ON r.customer_key = c.customer_key

    GROUP BY
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry,
        c.customer_status,
        c.is_ai_customer
),


support_risk AS (

    SELECT
        s.customer_key,

        COUNT(*) AS support_ticket_count,

        COALESCE(
            AVG(
                CASE
                    WHEN s.sla_met = TRUE
                        THEN 1.0
                    ELSE 0.0
                END
            ) * 100,
            100
        ) AS sla_compliance_pct,

        COALESCE(
            AVG(
                CASE
                    WHEN s.reopened = TRUE
                        THEN 1.0
                    ELSE 0.0
                END
            ) * 100,
            0
        ) AS reopen_rate_pct,

        COALESCE(
            AVG(s.resolution_hours),
            0
        ) AS avg_resolution_hours,

        COALESCE(
            AVG(s.customer_satisfaction),
            0
        ) AS avg_customer_satisfaction

    FROM warehouse.fact_support_ticket s

    GROUP BY
        s.customer_key
),


cloud_risk AS (

    SELECT
        u.customer_key,

        COALESCE(
            SUM(u.requests_count),
            0
        ) AS requests_count,

        COALESCE(
            SUM(u.failed_requests),
            0
        ) AS failed_requests,

        COALESCE(
            SUM(u.failed_requests)::NUMERIC
            /
            NULLIF(
                SUM(u.requests_count),
                0
            )
            * 100,
            0
        ) AS request_failure_rate_pct

    FROM warehouse.fact_cloud_usage u

    GROUP BY
        u.customer_key
),


renewal_risk AS (

    SELECT
        customer_id,

        MAX(
            renewal_risk_score
        ) AS renewal_risk_score

    FROM analytics.v_subscription_renewal_risk

    GROUP BY
        customer_id
),


combined AS (

    SELECT
        b.customer_key,
        b.customer_id,
        b.customer_name,
        b.customer_segment,
        b.industry,
        b.customer_status,
        b.is_ai_customer,
        b.lifetime_revenue_usd,

        COALESCE(
            r.renewal_risk_score,
            0
        ) AS renewal_risk_score,

        COALESCE(
            s.support_ticket_count,
            0
        ) AS support_ticket_count,

        COALESCE(
            s.sla_compliance_pct,
            100
        ) AS sla_compliance_pct,

        COALESCE(
            s.reopen_rate_pct,
            0
        ) AS reopen_rate_pct,

        COALESCE(
            s.avg_resolution_hours,
            0
        ) AS avg_resolution_hours,

        COALESCE(
            s.avg_customer_satisfaction,
            0
        ) AS avg_customer_satisfaction,

        COALESCE(
            c.requests_count,
            0
        ) AS requests_count,

        COALESCE(
            c.failed_requests,
            0
        ) AS failed_requests,

        COALESCE(
            c.request_failure_rate_pct,
            0
        ) AS request_failure_rate_pct

    FROM customer_base b

    LEFT JOIN renewal_risk r
        ON r.customer_id = b.customer_id

    LEFT JOIN support_risk s
        ON s.customer_key = b.customer_key

    LEFT JOIN cloud_risk c
        ON c.customer_key = b.customer_key
),


scored AS (

    SELECT
        *,

        LEAST(
            100::NUMERIC,

            GREATEST(
                0::NUMERIC,

                (
                    renewal_risk_score
                    * 0.50::NUMERIC
                )
                +
                (
                    (100::NUMERIC - sla_compliance_pct)
                    * 0.20::NUMERIC
                )
                +
                (
                    LEAST(
                        reopen_rate_pct,
                        100::NUMERIC
                    )
                    * 0.10::NUMERIC
                )
                +
                (
                    LEAST(
                        request_failure_rate_pct
                        * 10::NUMERIC,
                        100::NUMERIC
                    )
                    * 0.20::NUMERIC
                )
            )
        ) AS composite_risk_score

    FROM combined
),


risk_value AS (

    SELECT
        *,

        (
            lifetime_revenue_usd
            * composite_risk_score
            / 100::NUMERIC
        ) AS revenue_at_risk_usd

    FROM scored
)


SELECT
    customer_id,
    customer_name,
    customer_segment,
    industry,
    customer_status,
    is_ai_customer,

    ROUND(
        lifetime_revenue_usd,
        2
    ) AS lifetime_revenue_usd,

    ROUND(
        renewal_risk_score,
        2
    ) AS renewal_risk_score,

    support_ticket_count,

    ROUND(
        sla_compliance_pct,
        2
    ) AS sla_compliance_pct,

    ROUND(
        reopen_rate_pct,
        2
    ) AS reopen_rate_pct,

    ROUND(
        avg_resolution_hours,
        2
    ) AS avg_resolution_hours,

    ROUND(
        avg_customer_satisfaction,
        2
    ) AS avg_customer_satisfaction,

    requests_count,
    failed_requests,

    ROUND(
        request_failure_rate_pct,
        4
    ) AS request_failure_rate_pct,

    ROUND(
        composite_risk_score,
        2
    ) AS composite_risk_score,

    ROUND(
        revenue_at_risk_usd,
        2
    ) AS revenue_at_risk_usd,

    CASE
        WHEN composite_risk_score >= 75
            THEN 'Critical'

        WHEN composite_risk_score >= 50
            THEN 'High'

        WHEN composite_risk_score >= 25
            THEN 'Medium'

        ELSE
            'Low'
    END AS revenue_risk_band,

    RANK() OVER (
        ORDER BY
            revenue_at_risk_usd DESC
    ) AS revenue_at_risk_rank

FROM risk_value;