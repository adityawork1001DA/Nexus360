-- ============================================================
-- NEXUS 360
-- Q14 - Customer 360 Analytical View
--
-- Purpose:
--   Build a cross-domain customer intelligence layer.
--
-- Domains:
--   CRM
--   Revenue
--   Subscription
--   Support
--   Cloud usage
--
-- Skills:
--   multiple CTEs
--   cross-domain aggregation
--   LEFT JOIN
--   FILTER
--   COALESCE
--   customer-level semantic modeling
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_customer_360 AS

WITH revenue AS (

    SELECT
        customer_key,

        SUM(
            net_revenue_usd
        ) AS lifetime_revenue_usd,

        SUM(
            gross_profit_usd
        ) AS lifetime_gross_profit_usd,

        COUNT(
            DISTINCT transaction_id
        ) AS transactions,

        COUNT(
            DISTINCT product_key
        ) AS purchased_products

    FROM warehouse.fact_revenue

    GROUP BY customer_key
),

subscriptions AS (

    SELECT
        customer_key,

        COUNT(
            DISTINCT subscription_id
        ) AS subscriptions,

        COUNT(
            DISTINCT subscription_id
        ) FILTER (
            WHERE subscription_status = 'Active'
        ) AS active_subscriptions,

        SUM(
            contract_value_usd
        ) FILTER (
            WHERE subscription_status = 'Active'
        ) AS active_contract_value_usd

    FROM warehouse.fact_subscription

    GROUP BY customer_key
),

support AS (

    SELECT
        customer_key,

        COUNT(*) AS support_tickets,

        COUNT(*) FILTER (
            WHERE sla_met = FALSE
        ) AS sla_breaches,

        COUNT(*) FILTER (
            WHERE reopened = TRUE
        ) AS reopened_tickets,

        AVG(
            resolution_hours
        ) AS avg_resolution_hours,

        AVG(
            customer_satisfaction
        ) AS avg_customer_satisfaction

    FROM warehouse.fact_support_ticket

    GROUP BY customer_key
),

usage AS (

    SELECT
        customer_key,

        SUM(
            compute_hours
        ) AS compute_hours,

        SUM(
            storage_gb
        ) AS storage_gb,

        SUM(
            network_gb
        ) AS network_gb,

        SUM(
            ai_tokens_million
        ) AS ai_tokens_million,

        SUM(
            requests_count
        ) AS requests_count,

        SUM(
            failed_requests
        ) AS failed_requests,

        SUM(
            estimated_cost_usd
        ) AS cloud_cost_usd

    FROM warehouse.fact_cloud_usage

    GROUP BY customer_key
)

SELECT
    c.customer_id,
    c.customer_name,
    c.industry,
    c.customer_segment,
    c.employee_band,
    c.annual_revenue_band,
    c.acquisition_channel,
    c.signup_date,
    c.customer_status,
    c.is_ai_customer,

    ROUND(
        COALESCE(
            r.lifetime_revenue_usd,
            0
        ),
        2
    ) AS lifetime_revenue_usd,

    ROUND(
        COALESCE(
            r.lifetime_gross_profit_usd,
            0
        ),
        2
    ) AS lifetime_gross_profit_usd,

    COALESCE(
        r.transactions,
        0
    ) AS transactions,

    COALESCE(
        r.purchased_products,
        0
    ) AS purchased_products,

    COALESCE(
        sub.subscriptions,
        0
    ) AS subscriptions,

    COALESCE(
        sub.active_subscriptions,
        0
    ) AS active_subscriptions,

    ROUND(
        COALESCE(
            sub.active_contract_value_usd,
            0
        ),
        2
    ) AS active_contract_value_usd,

    COALESCE(
        sup.support_tickets,
        0
    ) AS support_tickets,

    COALESCE(
        sup.sla_breaches,
        0
    ) AS sla_breaches,

    COALESCE(
        sup.reopened_tickets,
        0
    ) AS reopened_tickets,

    ROUND(
        COALESCE(
            sup.avg_resolution_hours,
            0
        ),
        2
    ) AS avg_resolution_hours,

    ROUND(
        COALESCE(
            sup.avg_customer_satisfaction,
            0
        ),
        2
    ) AS avg_customer_satisfaction,

    ROUND(
        COALESCE(
            u.compute_hours,
            0
        ),
        2
    ) AS compute_hours,

    ROUND(
        COALESCE(
            u.storage_gb,
            0
        ),
        2
    ) AS storage_gb,

    ROUND(
        COALESCE(
            u.network_gb,
            0
        ),
        2
    ) AS network_gb,

    ROUND(
        COALESCE(
            u.ai_tokens_million,
            0
        ),
        2
    ) AS ai_tokens_million,

    COALESCE(
        u.requests_count,
        0
    ) AS requests_count,

    COALESCE(
        u.failed_requests,
        0
    ) AS failed_requests,

    ROUND(
        COALESCE(
            u.failed_requests,
            0
        )::NUMERIC

        / NULLIF(
            COALESCE(
                u.requests_count,
                0
            ),
            0
        )

        * 100,
        4
    ) AS request_failure_rate_pct,

    ROUND(
        COALESCE(
            u.cloud_cost_usd,
            0
        ),
        2
    ) AS cloud_cost_usd

FROM warehouse.dim_customer c

LEFT JOIN revenue r
    ON r.customer_key = c.customer_key

LEFT JOIN subscriptions sub
    ON sub.customer_key = c.customer_key

LEFT JOIN support sup
    ON sup.customer_key = c.customer_key

LEFT JOIN usage u
    ON u.customer_key = c.customer_key;