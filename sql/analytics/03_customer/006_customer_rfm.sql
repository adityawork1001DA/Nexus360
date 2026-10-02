-- ============================================================
-- NEXUS 360
-- Q06 - RFM Customer Segmentation
--
-- R = Recency
-- F = Frequency
-- M = Monetary Value
--
-- Skills:
--   CTE
--   date arithmetic
--   COUNT DISTINCT
--   NTILE
--   behavioral segmentation
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_customer_rfm AS

WITH reference_date AS (

    SELECT
        MAX(
            d.full_date
        ) AS analysis_date

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_date d
        ON d.date_key = f.date_key
),

customer_metrics AS (

    SELECT
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry,

        MAX(
            d.full_date
        ) AS last_purchase_date,

        COUNT(
            DISTINCT f.transaction_id
        ) AS purchase_frequency,

        SUM(
            f.net_revenue_usd
        ) AS monetary_value,

        SUM(
            f.gross_profit_usd
        ) AS gross_profit_value

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_customer c
        ON c.customer_key = f.customer_key

    JOIN warehouse.dim_date d
        ON d.date_key = f.date_key

    GROUP BY
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.customer_segment,
        c.industry
),

rfm_base AS (

    SELECT
        cm.*,

        (
            rd.analysis_date
            - cm.last_purchase_date
        ) AS recency_days

    FROM customer_metrics cm

    CROSS JOIN reference_date rd
),

scores AS (

    SELECT
        *,

        NTILE(5) OVER (
            ORDER BY recency_days DESC
        ) AS recency_score,

        NTILE(5) OVER (
            ORDER BY purchase_frequency ASC
        ) AS frequency_score,

        NTILE(5) OVER (
            ORDER BY monetary_value ASC
        ) AS monetary_score

    FROM rfm_base
)

SELECT
    customer_id,
    customer_name,
    customer_segment,
    industry,

    last_purchase_date,
    recency_days,
    purchase_frequency,

    ROUND(
        monetary_value,
        2
    ) AS monetary_value,

    ROUND(
        gross_profit_value,
        2
    ) AS gross_profit_value,

    recency_score,
    frequency_score,
    monetary_score,

    (
        recency_score
        + frequency_score
        + monetary_score
    ) AS rfm_total_score,

    CONCAT(
        recency_score,
        frequency_score,
        monetary_score
    ) AS rfm_code,

    CASE

        WHEN
            recency_score >= 4
            AND frequency_score >= 4
            AND monetary_score >= 4
        THEN 'Champions'

        WHEN
            recency_score >= 3
            AND frequency_score >= 4
        THEN 'Loyal Customers'

        WHEN
            recency_score >= 4
            AND frequency_score <= 2
        THEN 'Promising'

        WHEN
            recency_score <= 2
            AND frequency_score >= 4
            AND monetary_score >= 4
        THEN 'At Risk High Value'

        WHEN
            recency_score <= 2
            AND frequency_score <= 2
        THEN 'Hibernating'

        ELSE 'Regular Customers'

    END AS rfm_segment

FROM scores;