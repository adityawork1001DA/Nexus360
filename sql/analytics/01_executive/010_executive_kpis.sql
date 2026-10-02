-- ============================================================
-- NEXUS 360
-- Q10 - Executive KPI Snapshot
--
-- Purpose:
--   Central KPI semantic layer for:
--     Streamlit
--     Tableau
--     Excel
--     Python
--     Gemini Copilot
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_executive_kpis AS

WITH revenue_metrics AS (

    SELECT
        SUM(
            net_revenue_usd
        ) AS total_revenue,

        SUM(
            estimated_cost_usd
        ) AS total_estimated_cost,

        SUM(
            gross_profit_usd
        ) AS total_gross_profit,

        COUNT(
            DISTINCT transaction_id
        ) AS transactions,

        COUNT(
            DISTINCT customer_key
        ) AS revenue_customers

    FROM warehouse.fact_revenue
),

customer_metrics AS (

    SELECT
        COUNT(*) AS total_customers,

        COUNT(*) FILTER (
            WHERE customer_status = 'Active'
        ) AS active_customers,

        COUNT(*) FILTER (
            WHERE is_ai_customer = TRUE
        ) AS ai_customers

    FROM warehouse.dim_customer
),

subscription_metrics AS (

    SELECT
        COUNT(*) AS subscriptions,

        COUNT(*) FILTER (
            WHERE subscription_status = 'Active'
        ) AS active_subscriptions,

        SUM(
            contract_value_usd
        ) AS total_contract_value_usd,

        SUM(
            contract_value_usd
        ) FILTER (
            WHERE subscription_status = 'Active'
        ) AS active_contract_value_usd

    FROM warehouse.fact_subscription
),

support_metrics AS (

    SELECT
        COUNT(*) AS total_tickets,

        COUNT(*) FILTER (
            WHERE sla_met = TRUE
        ) AS sla_met_tickets,

        AVG(
            resolution_hours
        ) AS avg_resolution_hours,

        AVG(
            customer_satisfaction
        ) AS avg_customer_satisfaction,

        COUNT(*) FILTER (
            WHERE reopened = TRUE
        ) AS reopened_tickets

    FROM warehouse.fact_support_ticket
),

usage_metrics AS (

    SELECT
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
        ) AS api_requests,

        SUM(
            failed_requests
        ) AS failed_requests,

        SUM(
            estimated_cost_usd
        ) AS cloud_estimated_cost_usd,

        SUM(
            carbon_estimate_kg
        ) AS carbon_estimate_kg

    FROM warehouse.fact_cloud_usage
)

SELECT
    ROUND(
        r.total_revenue,
        2
    ) AS total_revenue_usd,

    ROUND(
        r.total_estimated_cost,
        2
    ) AS total_estimated_cost_usd,

    ROUND(
        r.total_gross_profit,
        2
    ) AS total_gross_profit_usd,

    ROUND(
        r.total_gross_profit
        / NULLIF(
            r.total_revenue,
            0
        )
        * 100,
        2
    ) AS gross_margin_pct,

    r.transactions,

    c.total_customers,
    c.active_customers,
    c.ai_customers,

    ROUND(
        r.total_revenue
        / NULLIF(
            r.revenue_customers,
            0
        ),
        2
    ) AS avg_revenue_per_customer,

    sub.subscriptions,
    sub.active_subscriptions,

    ROUND(
        sub.total_contract_value_usd,
        2
    ) AS total_contract_value_usd,

    ROUND(
        sub.active_contract_value_usd,
        2
    ) AS active_contract_value_usd,

    s.total_tickets,

    ROUND(
        s.sla_met_tickets::NUMERIC
        / NULLIF(
            s.total_tickets,
            0
        )
        * 100,
        2
    ) AS sla_compliance_pct,

    ROUND(
        s.avg_resolution_hours,
        2
    ) AS avg_resolution_hours,

    ROUND(
        s.avg_customer_satisfaction,
        2
    ) AS avg_customer_satisfaction,

    ROUND(
        s.reopened_tickets::NUMERIC
        / NULLIF(
            s.total_tickets,
            0
        )
        * 100,
        2
    ) AS ticket_reopen_rate_pct,

    ROUND(
        u.compute_hours,
        2
    ) AS total_compute_hours,

    ROUND(
        u.storage_gb,
        2
    ) AS total_storage_gb,

    ROUND(
        u.network_gb,
        2
    ) AS total_network_gb,

    ROUND(
        u.ai_tokens_million,
        2
    ) AS total_ai_tokens_million,

    u.api_requests,

    u.failed_requests,

    ROUND(
        u.failed_requests::NUMERIC
        / NULLIF(
            u.api_requests,
            0
        )
        * 100,
        4
    ) AS request_failure_rate_pct,

    ROUND(
        u.cloud_estimated_cost_usd,
        2
    ) AS cloud_estimated_cost_usd,

    ROUND(
        u.carbon_estimate_kg,
        2
    ) AS carbon_estimate_kg

FROM revenue_metrics r

CROSS JOIN customer_metrics c

CROSS JOIN subscription_metrics sub

CROSS JOIN support_metrics s

CROSS JOIN usage_metrics u;