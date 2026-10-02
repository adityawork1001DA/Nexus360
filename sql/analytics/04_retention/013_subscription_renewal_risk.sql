-- ============================================================
-- NEXUS 360
-- Q13 - Subscription Renewal Risk
--
-- Purpose:
--   Identify subscriptions that may require retention
--   intervention.
--
-- Important:
--   This is an analytical rules-based risk signal,
--   NOT the ML churn model. ML comes later.
--
-- Skills:
--   multi-table joins
--   CASE
--   scoring
--   date dimensions
--   business-rule analytics
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_subscription_renewal_risk AS

WITH subscription_base AS (

    SELECT
        s.subscription_key,
        s.subscription_id,

        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry,

        p.product_code,
        p.product_name,
        p.product_family,

        start_date.full_date
            AS subscription_start_date,

        end_date.full_date
            AS subscription_end_date,

        s.billing_frequency,
        s.contract_value_usd,
        s.seats,
        s.subscription_status,
        s.auto_renew

    FROM warehouse.fact_subscription s

    JOIN warehouse.dim_customer c
        ON c.customer_key = s.customer_key

    JOIN warehouse.dim_product p
        ON p.product_key = s.product_key

    LEFT JOIN warehouse.dim_date start_date
        ON start_date.date_key =
           s.start_date_key

    LEFT JOIN warehouse.dim_date end_date
        ON end_date.date_key =
           s.end_date_key
),

scored AS (

    SELECT
        *,

        (
            CASE
                WHEN auto_renew = FALSE
                THEN 35
                ELSE 0
            END

            +

            CASE
                WHEN subscription_status <> 'Active'
                THEN 30
                ELSE 0
            END

            +

            CASE
                WHEN subscription_end_date
                     IS NOT NULL
                     AND subscription_end_date
                         <= CURRENT_DATE + 90
                     AND subscription_end_date
                         >= CURRENT_DATE
                THEN 20
                ELSE 0
            END

            +

            CASE
                WHEN seats <= 10
                THEN 5
                ELSE 0
            END

        ) AS renewal_risk_score

    FROM subscription_base
)

SELECT
    subscription_id,

    customer_id,
    customer_name,
    customer_segment,
    industry,

    product_code,
    product_name,
    product_family,

    subscription_start_date,
    subscription_end_date,

    billing_frequency,

    ROUND(
        contract_value_usd,
        2
    ) AS contract_value_usd,

    seats,
    subscription_status,
    auto_renew,

    renewal_risk_score,

    CASE

        WHEN renewal_risk_score >= 60
            THEN 'Critical'

        WHEN renewal_risk_score >= 35
            THEN 'High'

        WHEN renewal_risk_score >= 20
            THEN 'Medium'

        ELSE 'Low'

    END AS renewal_risk_band

FROM scored;