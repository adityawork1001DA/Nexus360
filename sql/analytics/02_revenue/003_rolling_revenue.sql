-- ============================================================
-- NEXUS 360
-- Q03 - Rolling Revenue Analytics
--
-- Skills:
--   rolling averages
--   rolling sums
--   STDDEV
--   window frames
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_rolling_revenue AS

WITH monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::DATE AS revenue_month,

        SUM(
            f.net_revenue_usd
        ) AS revenue_usd,

        SUM(
            f.gross_profit_usd
        ) AS gross_profit_usd

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_date d
        ON d.date_key = f.date_key

    GROUP BY 1
)

SELECT
    revenue_month,

    ROUND(
        revenue_usd,
        2
    ) AS revenue_usd,

    ROUND(
        AVG(
            revenue_usd
        ) OVER (
            ORDER BY revenue_month
            ROWS BETWEEN
                2 PRECEDING
                AND CURRENT ROW
        ),
        2
    ) AS rolling_3m_avg,

    ROUND(
        AVG(
            revenue_usd
        ) OVER (
            ORDER BY revenue_month
            ROWS BETWEEN
                5 PRECEDING
                AND CURRENT ROW
        ),
        2
    ) AS rolling_6m_avg,

    ROUND(
        SUM(
            revenue_usd
        ) OVER (
            ORDER BY revenue_month
            ROWS BETWEEN
                11 PRECEDING
                AND CURRENT ROW
        ),
        2
    ) AS rolling_12m_revenue,

    ROUND(
        STDDEV_SAMP(
            revenue_usd
        ) OVER (
            ORDER BY revenue_month
            ROWS BETWEEN
                5 PRECEDING
                AND CURRENT ROW
        ),
        2
    ) AS rolling_6m_volatility,

    ROUND(
        SUM(
            gross_profit_usd
        ) OVER (
            ORDER BY revenue_month
            ROWS BETWEEN
                11 PRECEDING
                AND CURRENT ROW
        ),
        2
    ) AS rolling_12m_gross_profit

FROM monthly;