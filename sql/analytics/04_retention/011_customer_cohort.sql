-- ============================================================
-- NEXUS 360
-- Q11 - Customer Acquisition Cohort Analytics
--
-- Purpose:
--   Analyze customers by signup cohort and determine
--   how many continue generating revenue over time.
--
-- Skills:
--   CTE
--   DATE_TRUNC
--   cohort analysis
--   date arithmetic
--   conditional aggregation
--   safe division
-- ============================================================

CREATE OR REPLACE VIEW analytics.v_customer_cohort AS

WITH customer_cohort AS (

    SELECT
        customer_key,

        DATE_TRUNC(
            'month',
            signup_date
        )::DATE AS cohort_month

    FROM warehouse.dim_customer

    WHERE signup_date IS NOT NULL
),

customer_activity AS (

    SELECT DISTINCT
        f.customer_key,

        DATE_TRUNC(
            'month',
            d.full_date
        )::DATE AS activity_month

    FROM warehouse.fact_revenue f

    JOIN warehouse.dim_date d
        ON d.date_key = f.date_key
),

cohort_activity AS (

    SELECT
        cc.customer_key,
        cc.cohort_month,
        ca.activity_month,

        (
            EXTRACT(
                YEAR
                FROM AGE(
                    ca.activity_month,
                    cc.cohort_month
                )
            ) * 12

            +

            EXTRACT(
                MONTH
                FROM AGE(
                    ca.activity_month,
                    cc.cohort_month
                )
            )
        )::INTEGER AS months_since_signup

    FROM customer_cohort cc

    JOIN customer_activity ca
        ON ca.customer_key = cc.customer_key

    WHERE
        ca.activity_month >= cc.cohort_month
),

cohort_size AS (

    SELECT
        cohort_month,

        COUNT(
            DISTINCT customer_key
        ) AS cohort_customers

    FROM customer_cohort

    GROUP BY cohort_month
),

retention AS (

    SELECT
        cohort_month,
        months_since_signup,

        COUNT(
            DISTINCT customer_key
        ) AS active_customers

    FROM cohort_activity

    GROUP BY
        cohort_month,
        months_since_signup
)

SELECT
    r.cohort_month,
    r.months_since_signup,

    cs.cohort_customers,

    r.active_customers,

    ROUND(
        r.active_customers::NUMERIC
        / NULLIF(
            cs.cohort_customers,
            0
        )
        * 100,
        2
    ) AS retention_pct

FROM retention r

JOIN cohort_size cs
    ON cs.cohort_month = r.cohort_month;