-- ============================================================
-- NEXUS 360
-- Q12 - Subscription Health
--
-- Purpose:
--   Analyze subscription portfolio health by product.
--
-- Skills:
--   FILTER
--   conditional aggregation
--   dimensional joins
--   safe percentages
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_subscription_health AS

SELECT
    p.product_code,
    p.product_name,
    p.product_family,
    p.service_category,
    p.is_ai_service,

    COUNT(
        DISTINCT s.subscription_id
    ) AS total_subscriptions,

    COUNT(
        DISTINCT s.subscription_id
    ) FILTER (
        WHERE s.subscription_status = 'Active'
    ) AS active_subscriptions,

    COUNT(
        DISTINCT s.subscription_id
    ) FILTER (
        WHERE s.auto_renew = TRUE
    ) AS auto_renew_subscriptions,

    SUM(
        s.contract_value_usd
    ) AS total_contract_value_usd,

    SUM(
        s.contract_value_usd
    ) FILTER (
        WHERE s.subscription_status = 'Active'
    ) AS active_contract_value_usd,

    SUM(
        s.seats
    ) FILTER (
        WHERE s.subscription_status = 'Active'
    ) AS active_seats,

    ROUND(
        COUNT(
            DISTINCT s.subscription_id
        ) FILTER (
            WHERE s.subscription_status = 'Active'
        )::NUMERIC

        / NULLIF(
            COUNT(
                DISTINCT s.subscription_id
            ),
            0
        )

        * 100,
        2
    ) AS active_subscription_pct,

    ROUND(
        COUNT(
            DISTINCT s.subscription_id
        ) FILTER (
            WHERE s.auto_renew = TRUE
        )::NUMERIC

        / NULLIF(
            COUNT(
                DISTINCT s.subscription_id
            ),
            0
        )

        * 100,
        2
    ) AS auto_renew_pct

FROM warehouse.fact_subscription s

JOIN warehouse.dim_product p
    ON p.product_key = s.product_key

GROUP BY
    p.product_code,
    p.product_name,
    p.product_family,
    p.service_category,
    p.is_ai_service;