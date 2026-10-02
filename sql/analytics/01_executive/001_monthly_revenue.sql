-- ============================================================
-- NEXUS 360
-- Q01 - Monthly Executive Revenue Performance
--
-- Grain:
--   One row per calendar month
--
-- Skills:
--   CTE
--   DATE_TRUNC
--   aggregation
--   LAG
--   running totals
--   margin analysis
--   safe division
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_monthly_revenue AS

WITH monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::DATE AS revenue_month,

        SUM(
            f.net_revenue_usd
        ) AS net_revenue_usd,

        SUM(
            f.estimated_cost_usd
        ) AS estimated_cost_usd,

        SUM(
            f.gross_profit_usd
        ) AS gross_profit_usd,

        COUNT(
            DISTINCT f.transaction_id
        ) AS transaction_count,

        COUNT(
            DISTINCT f.customer_key
        ) AS active_customers,

        COUNT(
            DISTINCT f.product_key
        ) AS active_products

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_date d
        ON d.date_key = f.date_key

    GROUP BY 1
),

growth AS (

    SELECT
        *,

        LAG(
            net_revenue_usd
        ) OVER (
            ORDER BY revenue_month
        ) AS previous_month_revenue

    FROM monthly
)

SELECT
    revenue_month,

    ROUND(
        net_revenue_usd,
        2
    ) AS net_revenue_usd,

    ROUND(
        estimated_cost_usd,
        2
    ) AS estimated_cost_usd,

    ROUND(
        gross_profit_usd,
        2
    ) AS gross_profit_usd,

    transaction_count,

    active_customers,

    active_products,

    ROUND(
        net_revenue_usd
        / NULLIF(active_customers, 0),
        2
    ) AS revenue_per_active_customer,

    ROUND(
        gross_profit_usd
        / NULLIF(net_revenue_usd, 0)
        * 100,
        2
    ) AS gross_margin_pct,

    ROUND(
        (
            net_revenue_usd
            - previous_month_revenue
        )
        / NULLIF(
            previous_month_revenue,
            0
        )
        * 100,
        2
    ) AS mom_growth_pct,

    ROUND(
        SUM(
            net_revenue_usd
        ) OVER (
            ORDER BY revenue_month
            ROWS BETWEEN
                UNBOUNDED PRECEDING
                AND CURRENT ROW
        ),
        2
    ) AS cumulative_revenue_usd

FROM growth;