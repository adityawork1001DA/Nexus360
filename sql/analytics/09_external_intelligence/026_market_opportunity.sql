-- ============================================================
-- NEXUS 360
-- Q26 - Market Opportunity Index
--
-- Purpose:
--   Identify countries with strong economic and digital
--   fundamentals but comparatively low current Nexus 360
--   commercial penetration.
--
-- Inputs:
--   analytics.v_macroeconomic_revenue
--
-- Demonstrates:
--   PERCENT_RANK
--   normalization
--   composite scoring
--   weighted business scoring
--   CASE segmentation
--   strategic market prioritization
--
-- PostgreSQL note:
--   PERCENT_RANK() returns DOUBLE PRECISION.
--   Values are explicitly cast to NUMERIC before using
--   ROUND(value, scale).
-- ============================================================

DROP VIEW IF EXISTS analytics.v_market_opportunity;

CREATE VIEW analytics.v_market_opportunity AS

WITH base AS (

    SELECT
        country_code,
        country_name,
        continent,
        income_group,

        total_customers,
        ai_customers,

        net_revenue_usd,

        gdp_usd,
        population,
        gdp_per_capita_usd,
        internet_users_pct,
        inflation_pct,

        revenue_per_capita_usd,
        ai_customer_adoption_pct

    FROM analytics.v_macroeconomic_revenue

    WHERE
        gdp_usd IS NOT NULL
        AND population IS NOT NULL
        AND gdp_per_capita_usd IS NOT NULL
        AND internet_users_pct IS NOT NULL
),

normalized AS (

    SELECT
        *,

        (
            PERCENT_RANK() OVER (
                ORDER BY gdp_usd
            ) * 100
        )::NUMERIC AS gdp_score,

        (
            PERCENT_RANK() OVER (
                ORDER BY gdp_per_capita_usd
            ) * 100
        )::NUMERIC AS wealth_score,

        (
            PERCENT_RANK() OVER (
                ORDER BY internet_users_pct
            ) * 100
        )::NUMERIC AS digital_score,

        (
            (
                1
                -
                PERCENT_RANK() OVER (
                    ORDER BY net_revenue_usd
                )
            ) * 100
        )::NUMERIC AS whitespace_score,

        (
            (
                1
                -
                PERCENT_RANK() OVER (
                    ORDER BY total_customers
                )
            ) * 100
        )::NUMERIC AS customer_whitespace_score

    FROM base
),

scored AS (

    SELECT
        *,

        (
            gdp_score * 0.25::NUMERIC
            +
            wealth_score * 0.15::NUMERIC
            +
            digital_score * 0.20::NUMERIC
            +
            whitespace_score * 0.25::NUMERIC
            +
            customer_whitespace_score * 0.15::NUMERIC
        )::NUMERIC AS market_opportunity_score

    FROM normalized
)

SELECT
    country_code,
    country_name,
    continent,
    income_group,

    total_customers,
    ai_customers,

    ROUND(
        net_revenue_usd,
        2
    ) AS net_revenue_usd,

    ROUND(
        gdp_usd,
        2
    ) AS gdp_usd,

    ROUND(
        population,
        0
    ) AS population,

    ROUND(
        gdp_per_capita_usd,
        2
    ) AS gdp_per_capita_usd,

    ROUND(
        internet_users_pct,
        4
    ) AS internet_users_pct,

    ROUND(
        inflation_pct,
        4
    ) AS inflation_pct,

    ROUND(
        ai_customer_adoption_pct,
        4
    ) AS ai_customer_adoption_pct,

    ROUND(
        gdp_score,
        2
    ) AS gdp_score,

    ROUND(
        wealth_score,
        2
    ) AS wealth_score,

    ROUND(
        digital_score,
        2
    ) AS digital_score,

    ROUND(
        whitespace_score,
        2
    ) AS whitespace_score,

    ROUND(
        customer_whitespace_score,
        2
    ) AS customer_whitespace_score,

    ROUND(
        market_opportunity_score,
        2
    ) AS market_opportunity_score,

    CASE
        WHEN market_opportunity_score >= 75
            THEN 'Strategic Priority'

        WHEN market_opportunity_score >= 60
            THEN 'High Opportunity'

        WHEN market_opportunity_score >= 40
            THEN 'Selective Expansion'

        ELSE
            'Mature / Lower Priority'
    END AS opportunity_band,

    RANK() OVER (
        ORDER BY
            market_opportunity_score DESC
    ) AS opportunity_rank

FROM scored;