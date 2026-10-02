-- ============================================================
-- Q05 - Customer Revenue Pareto Analysis
--
-- Business question:
-- What percentage of customers produces 80% of revenue?
--
-- Skills:
--   multiple CTEs
--   window functions
--   cumulative sums
--   Pareto analysis
--   percent-of-total
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_customer_pareto AS

WITH customer_revenue AS (

    SELECT
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.customer_segment,

        SUM(
            f.net_revenue_usd
        ) AS revenue_usd

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_customer c
        ON c.customer_key =
           f.customer_key

    GROUP BY
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.customer_segment
),

ranked AS (

    SELECT
        *,

        ROW_NUMBER() OVER (
            ORDER BY revenue_usd DESC
        ) AS customer_rank,

        COUNT(*) OVER ()
            AS total_customers,

        SUM(
            revenue_usd
        ) OVER ()
            AS total_revenue,

        SUM(
            revenue_usd
        ) OVER (
            ORDER BY revenue_usd DESC

            ROWS BETWEEN
                UNBOUNDED PRECEDING
                AND CURRENT ROW
        ) AS cumulative_revenue

    FROM customer_revenue
)

SELECT
    customer_id,
    customer_name,
    customer_segment,

    ROUND(
        revenue_usd,
        2
    ) AS revenue_usd,

    customer_rank,

    ROUND(
        customer_rank::NUMERIC
        / NULLIF(
            total_customers,
            0
        )
        * 100,
        2
    ) AS cumulative_customer_pct,

    ROUND(
        cumulative_revenue
        / NULLIF(
            total_revenue,
            0
        )
        * 100,
        2
    ) AS cumulative_revenue_pct,

    CASE
        WHEN
            cumulative_revenue
            / NULLIF(
                total_revenue,
                0
            )
            <= 0.80
        THEN 'Top 80% Revenue Group'

        ELSE 'Remaining Revenue Group'
    END AS pareto_group

FROM ranked;