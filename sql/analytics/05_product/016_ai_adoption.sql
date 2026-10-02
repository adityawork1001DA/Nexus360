-- ============================================================
-- NEXUS 360
-- Q16 - AI Adoption Intelligence
--
-- Purpose:
--   Analyze AI customer adoption and monetization.
--
-- Skills:
--   FILTER
--   conditional aggregation
--   segmentation
--   cross-domain analysis
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_ai_adoption AS

WITH customer_metrics AS (

    SELECT
        c.customer_key,
        c.customer_segment,
        c.industry,
        c.is_ai_customer,

        COALESCE(
            SUM(
                f.net_revenue_usd
            ),
            0
        ) AS revenue_usd,

        COALESCE(
            SUM(
                f.gross_profit_usd
            ),
            0
        ) AS gross_profit_usd

    FROM warehouse.dim_customer c

    LEFT JOIN warehouse.fact_revenue f
        ON f.customer_key = c.customer_key

    GROUP BY
        c.customer_key,
        c.customer_segment,
        c.industry,
        c.is_ai_customer
)

SELECT
    customer_segment,
    industry,

    COUNT(*) AS customers,

    COUNT(*) FILTER (
        WHERE is_ai_customer = TRUE
    ) AS ai_customers,

    ROUND(
        COUNT(*) FILTER (
            WHERE is_ai_customer = TRUE
        )::NUMERIC

        / NULLIF(
            COUNT(*),
            0
        )

        * 100,
        2
    ) AS ai_adoption_pct,

    ROUND(
        SUM(
            revenue_usd
        ),
        2
    ) AS total_revenue_usd,

    ROUND(
        SUM(
            revenue_usd
        ) FILTER (
            WHERE is_ai_customer = TRUE
        ),
        2
    ) AS ai_customer_revenue_usd,

    ROUND(
        AVG(
            revenue_usd
        ) FILTER (
            WHERE is_ai_customer = TRUE
        ),
        2
    ) AS avg_ai_customer_revenue_usd,

    ROUND(
        AVG(
            revenue_usd
        ) FILTER (
            WHERE is_ai_customer = FALSE
        ),
        2
    ) AS avg_non_ai_customer_revenue_usd,

    ROUND(
        SUM(
            gross_profit_usd
        ) FILTER (
            WHERE is_ai_customer = TRUE
        ),
        2
    ) AS ai_customer_gross_profit_usd

FROM customer_metrics

GROUP BY
    customer_segment,
    industry;