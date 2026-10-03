-- ============================================================
-- NEXUS 360
-- Q24 - FX Exposure & Currency Risk Intelligence
--
-- Business Question:
--   Which currencies create the greatest revenue and foreign
--   exchange exposure for the business?
--
-- Demonstrates:
--   CTE
--   aggregation
--   dimensional joins
--   window functions
--   STDDEV_POP
--   coefficient of variation
--   exposure concentration
--   risk scoring
--   CASE segmentation
-- ============================================================

DROP VIEW IF EXISTS analytics.v_fx_exposure;

CREATE VIEW analytics.v_fx_exposure AS

WITH revenue_by_currency AS (

    SELECT
        c.currency_key,
        c.currency_code,
        c.currency_name,

        COUNT(
            DISTINCT r.transaction_id
        ) AS transaction_count,

        COUNT(
            DISTINCT r.customer_key
        ) AS customer_count,

        COALESCE(
            SUM(r.net_revenue_local),
            0
        ) AS net_revenue_local,

        COALESCE(
            SUM(r.net_revenue_usd),
            0
        ) AS net_revenue_usd,

        AVG(
            r.fx_rate_to_usd
        ) AS average_transaction_fx_rate

    FROM warehouse.dim_currency c

    LEFT JOIN warehouse.fact_revenue r
        ON r.currency_key = c.currency_key

    WHERE c.active_flag = TRUE

    GROUP BY
        c.currency_key,
        c.currency_code,
        c.currency_name
),

fx_statistics AS (

    SELECT
        c.currency_key,

        COUNT(fx.fx_rate_key)
            AS fx_observation_count,

        AVG(fx.rate_to_usd)
            AS average_market_fx_rate,

        MIN(fx.rate_to_usd)
            AS minimum_fx_rate,

        MAX(fx.rate_to_usd)
            AS maximum_fx_rate,

        STDDEV_POP(fx.rate_to_usd)
            AS fx_volatility,

        CASE
            WHEN AVG(fx.rate_to_usd) = 0
                THEN NULL
            ELSE
                STDDEV_POP(fx.rate_to_usd)
                / NULLIF(
                    ABS(AVG(fx.rate_to_usd)),
                    0
                )
                * 100
        END AS fx_coefficient_variation_pct

    FROM warehouse.dim_currency c

    LEFT JOIN warehouse.fact_fx_rate fx
        ON fx.currency_key = c.currency_key

    WHERE c.active_flag = TRUE

    GROUP BY
        c.currency_key
),

combined AS (

    SELECT
        r.currency_code,
        r.currency_name,

        r.transaction_count,
        r.customer_count,

        r.net_revenue_local,
        r.net_revenue_usd,

        r.average_transaction_fx_rate,

        f.fx_observation_count,
        f.average_market_fx_rate,
        f.minimum_fx_rate,
        f.maximum_fx_rate,
        f.fx_volatility,
        f.fx_coefficient_variation_pct,

        r.net_revenue_usd
        / NULLIF(
            SUM(r.net_revenue_usd) OVER (),
            0
        )
        * 100 AS revenue_exposure_pct

    FROM revenue_by_currency r

    LEFT JOIN fx_statistics f
        ON f.currency_key = r.currency_key
),

scored AS (

    SELECT
        *,

        (
            COALESCE(revenue_exposure_pct, 0) * 0.60
            +
            LEAST(
                COALESCE(
                    fx_coefficient_variation_pct,
                    0
                ),
                100
            ) * 0.40
        ) AS fx_risk_score

    FROM combined
)

SELECT
    currency_code,
    currency_name,

    transaction_count,
    customer_count,

    ROUND(
        net_revenue_local,
        2
    ) AS net_revenue_local,

    ROUND(
        net_revenue_usd,
        2
    ) AS net_revenue_usd,

    ROUND(
        revenue_exposure_pct,
        4
    ) AS revenue_exposure_pct,

    ROUND(
        average_transaction_fx_rate,
        6
    ) AS average_transaction_fx_rate,

    fx_observation_count,

    ROUND(
        average_market_fx_rate,
        6
    ) AS average_market_fx_rate,

    ROUND(
        minimum_fx_rate,
        6
    ) AS minimum_fx_rate,

    ROUND(
        maximum_fx_rate,
        6
    ) AS maximum_fx_rate,

    ROUND(
        fx_volatility,
        6
    ) AS fx_volatility,

    ROUND(
        fx_coefficient_variation_pct,
        4
    ) AS fx_coefficient_variation_pct,

    ROUND(
        fx_risk_score,
        4
    ) AS fx_risk_score,

    CASE
        WHEN fx_risk_score >= 40
            THEN 'Critical'

        WHEN fx_risk_score >= 25
            THEN 'High'

        WHEN fx_risk_score >= 10
            THEN 'Medium'

        ELSE 'Low'
    END AS fx_risk_band,

    RANK() OVER (
        ORDER BY
            net_revenue_usd DESC
    ) AS revenue_exposure_rank,

    RANK() OVER (
        ORDER BY
            fx_risk_score DESC
    ) AS fx_risk_rank

FROM scored;