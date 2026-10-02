-- ============================================================
-- Q02 - Year-over-Year Revenue Growth
--
-- Skills:
--   CTE
--   DATE_TRUNC
--   LAG
--   partitioned window
--   YoY growth
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_yoy_revenue_growth AS

WITH monthly AS (

    SELECT
        EXTRACT(
            YEAR FROM d.full_date
        )::INTEGER AS year_number,

        EXTRACT(
            MONTH FROM d.full_date
        )::INTEGER AS month_number,

        DATE_TRUNC(
            'month',
            d.full_date
        )::DATE AS revenue_month,

        SUM(
            f.net_revenue_usd
        ) AS revenue_usd

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_date d
        ON d.date_key =
           f.date_key

    GROUP BY
        1,
        2,
        3
),

comparison AS (

    SELECT
        *,

        LAG(
            revenue_usd
        ) OVER (
            PARTITION BY month_number
            ORDER BY year_number
        ) AS previous_year_revenue

    FROM monthly
)

SELECT
    revenue_month,
    year_number,
    month_number,

    ROUND(
        revenue_usd,
        2
    ) AS revenue_usd,

    ROUND(
        previous_year_revenue,
        2
    ) AS previous_year_revenue_usd,

    ROUND(
        (
            revenue_usd
            - previous_year_revenue
        )
        / NULLIF(
            previous_year_revenue,
            0
        )
        * 100,
        2
    ) AS yoy_growth_pct

FROM comparison;