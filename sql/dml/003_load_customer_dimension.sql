INSERT INTO warehouse.dim_customer (
    customer_id,
    customer_name,
    industry,
    customer_segment,
    country_key,
    region_key,
    employee_band,
    annual_revenue_band,
    acquisition_channel,
    signup_date,
    customer_status,
    is_ai_customer,
    updated_at
)

SELECT
    s.customer_id,
    s.customer_name,
    s.industry,
    s.customer_segment,
    c.country_key,
    r.region_key,
    s.employee_band,
    s.annual_revenue_band,
    s.acquisition_channel,
    s.signup_date,
    s.customer_status,
    s.is_ai_customer,
    CURRENT_TIMESTAMP

FROM staging.customers s

JOIN warehouse.dim_country c
    ON c.country_code =
       s.country_code

JOIN warehouse.dim_region r
    ON r.region_code =
       s.region_code

ON CONFLICT (customer_id)

DO UPDATE SET
    customer_name =
        EXCLUDED.customer_name,

    industry =
        EXCLUDED.industry,

    customer_segment =
        EXCLUDED.customer_segment,

    country_key =
        EXCLUDED.country_key,

    region_key =
        EXCLUDED.region_key,

    employee_band =
        EXCLUDED.employee_band,

    annual_revenue_band =
        EXCLUDED.annual_revenue_band,

    acquisition_channel =
        EXCLUDED.acquisition_channel,

    customer_status =
        EXCLUDED.customer_status,

    is_ai_customer =
        EXCLUDED.is_ai_customer,

    updated_at =
        CURRENT_TIMESTAMP;