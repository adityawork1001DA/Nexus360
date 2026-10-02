-- ============================================================
-- NEXUS 360
-- Q09 - Daily Revenue Statistical Anomaly Detection
--
-- Skills:
--   statistical aggregation
--   STDDEV_SAMP
--   Z-score
--   anomaly classification
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_revenue_anomalies AS

WITH daily AS (

    SELECT
        d.full_date,

        SUM(
            f.net_revenue_usd
        ) AS daily_revenue,

        COUNT(
            DISTINCT f.transaction_id
        ) AS transactions

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_date d
        ON d.date_key = f.date_key

    GROUP BY
        d.full_date
),

statistics AS (

    SELECT
        AVG(
            daily_revenue
        ) AS mean_revenue,

        STDDEV_SAMP(
            daily_revenue
        ) AS revenue_stddev

    FROM daily
),

scored AS (

    SELECT
        d.full_date,
        d.daily_revenue,
        d.transactions,

        s.mean_revenue,
        s.revenue_stddev,

        (
            d.daily_revenue
            - s.mean_revenue
        )
        / NULLIF(
            s.revenue_stddev,
            0
        ) AS z_score

    FROM daily d

    CROSS JOIN statistics s
)

SELECT
    full_date,

    ROUND(
        daily_revenue,
        2
    ) AS daily_revenue,

    transactions,

    ROUND(
        mean_revenue,
        2
    ) AS mean_revenue,

    ROUND(
        revenue_stddev,
        2
    ) AS revenue_stddev,

    ROUND(
        z_score,
        3
    ) AS z_score,

    CASE

        WHEN ABS(z_score) >= 3
            THEN 'Critical Anomaly'

        WHEN ABS(z_score) >= 2
            THEN 'Potential Anomaly'

        ELSE 'Normal'

    END AS anomaly_status

FROM scored;