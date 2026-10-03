-- ============================================================
-- NEXUS 360
-- Q25 - Macroeconomic Revenue Intelligence
--
-- Purpose:
--   Combine internal customer/revenue performance with
--   external World Bank macroeconomic indicators.
--
-- Indicators:
--   NY.GDP.MKTP.CD  -> GDP current USD
--   SP.POP.TOTL     -> Population
--   NY.GDP.PCAP.CD  -> GDP per capita
--   IT.NET.USER.ZS  -> Internet usage %
--   FP.CPI.TOTL.ZG  -> Inflation %
--
-- Architecture:
--   This semantic view is consumed by downstream analytics,
--   especially analytics.v_market_opportunity.
--
-- IMPORTANT:
--   Do NOT DROP this view during normal analytics builds.
--   CREATE OR REPLACE preserves downstream dependencies.
--
--   Existing output column names, order and datatypes must
--   remain stable unless an explicit migration is performed.
-- ============================================================


CREATE OR REPLACE VIEW analytics.v_macroeconomic_revenue AS

WITH ranked_indicators AS (

    SELECT
        e.country_key,
        e.indicator_code,
        e.indicator_value,
        e.year_number,

        ROW_NUMBER() OVER (
            PARTITION BY
                e.country_key,
                e.indicator_code
            ORDER BY
                e.year_number DESC
        ) AS rn

    FROM warehouse.fact_economic_indicator e

    WHERE e.indicator_value IS NOT NULL
),


latest_indicators AS (

    SELECT
        country_key,

        MAX(indicator_value) FILTER (
            WHERE indicator_code = 'NY.GDP.MKTP.CD'
        ) AS gdp_usd,

        MAX(indicator_value) FILTER (
            WHERE indicator_code = 'SP.POP.TOTL'
        ) AS population,

        MAX(indicator_value) FILTER (
            WHERE indicator_code = 'NY.GDP.PCAP.CD'
        ) AS gdp_per_capita_usd,

        MAX(indicator_value) FILTER (
            WHERE indicator_code = 'IT.NET.USER.ZS'
        ) AS internet_users_pct,

        MAX(indicator_value) FILTER (
            WHERE indicator_code = 'FP.CPI.TOTL.ZG'
        ) AS inflation_pct,

        MAX(year_number) AS latest_economic_year

    FROM ranked_indicators

    WHERE rn = 1

    GROUP BY
        country_key
),


customer_country AS (

    SELECT
        c.country_key,

        COUNT(
            DISTINCT c.customer_key
        ) AS total_customers,

        COUNT(
            DISTINCT c.customer_key
        ) FILTER (
            WHERE c.is_ai_customer = TRUE
        ) AS ai_customers

    FROM warehouse.dim_customer c

    GROUP BY
        c.country_key
),


revenue_country AS (

    SELECT
        c.country_key,

        COUNT(
            DISTINCT r.transaction_id
        ) AS transaction_count,

        COUNT(
            DISTINCT r.customer_key
        ) AS revenue_customers,

        COALESCE(
            SUM(r.net_revenue_usd),
            0
        ) AS net_revenue_usd,

        COALESCE(
            SUM(r.gross_profit_usd),
            0
        ) AS gross_profit_usd

    FROM warehouse.fact_revenue r

    INNER JOIN warehouse.dim_customer c
        ON c.customer_key = r.customer_key

    GROUP BY
        c.country_key
)


SELECT
    co.country_code,
    co.country_name,
    co.continent,
    co.income_group,

    COALESCE(
        cc.total_customers,
        0
    ) AS total_customers,

    COALESCE(
        cc.ai_customers,
        0
    ) AS ai_customers,

    COALESCE(
        rc.transaction_count,
        0
    ) AS transaction_count,

    COALESCE(
        rc.revenue_customers,
        0
    ) AS revenue_customers,

    ROUND(
        COALESCE(
            rc.net_revenue_usd,
            0
        ),
        2
    ) AS net_revenue_usd,

    ROUND(
        COALESCE(
            rc.gross_profit_usd,
            0
        ),
        2
    ) AS gross_profit_usd,

    li.latest_economic_year,

    ROUND(
        li.gdp_usd,
        2
    ) AS gdp_usd,

    ROUND(
        li.population,
        0
    ) AS population,

    ROUND(
        li.gdp_per_capita_usd,
        2
    ) AS gdp_per_capita_usd,

    ROUND(
        li.internet_users_pct,
        4
    ) AS internet_users_pct,

    ROUND(
        li.inflation_pct,
        4
    ) AS inflation_pct,

    ROUND(
        COALESCE(
            rc.net_revenue_usd,
            0
        )
        / NULLIF(
            li.gdp_usd,
            0
        )
        * 1000000,
        6
    ) AS revenue_per_million_gdp,

    ROUND(
        COALESCE(
            rc.net_revenue_usd,
            0
        )
        / NULLIF(
            li.population,
            0
        ),
        6
    ) AS revenue_per_capita_usd,

    ROUND(
        COALESCE(
            cc.ai_customers,
            0
        )::NUMERIC
        / NULLIF(
            cc.total_customers,
            0
        )
        * 100,
        4
    ) AS ai_customer_adoption_pct

FROM warehouse.dim_country co

LEFT JOIN latest_indicators li
    ON li.country_key = co.country_key

LEFT JOIN customer_country cc
    ON cc.country_key = co.country_key

LEFT JOIN revenue_country rc
    ON rc.country_key = co.country_key

WHERE co.active_flag = TRUE;