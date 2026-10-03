INSERT INTO warehouse.fact_cloud_usage (
    usage_id,
    date_key,
    customer_key,
    product_key,
    region_key,
    datacenter_key,
    compute_hours,
    storage_gb,
    network_gb,
    ai_tokens_million,
    requests_count,
    failed_requests,
    estimated_cost_usd,
    carbon_estimate_kg
)

SELECT
    s.usage_id,

    TO_CHAR(
        s.usage_date,
        'YYYYMMDD'
    )::INTEGER,

    c.customer_key,
    p.product_key,
    r.region_key,
    dc.datacenter_key,

    s.compute_hours,
    s.storage_gb,
    s.network_gb,
    s.ai_tokens_million,
    s.requests_count,
    s.failed_requests,
    s.estimated_cost_usd,
    s.carbon_estimate_kg

FROM staging.cloud_usage s

JOIN warehouse.dim_customer c
    ON c.customer_id = s.customer_id

JOIN warehouse.dim_product p
    ON p.product_code = s.product_code

JOIN warehouse.dim_region r
    ON r.region_code = s.region_code

LEFT JOIN warehouse.dim_datacenter dc
    ON dc.datacenter_code = s.datacenter_code

ON CONFLICT (usage_id)

DO UPDATE SET
    date_key =
        EXCLUDED.date_key,

    customer_key =
        EXCLUDED.customer_key,

    product_key =
        EXCLUDED.product_key,

    region_key =
        EXCLUDED.region_key,

    datacenter_key =
        EXCLUDED.datacenter_key,

    compute_hours =
        EXCLUDED.compute_hours,

    storage_gb =
        EXCLUDED.storage_gb,

    network_gb =
        EXCLUDED.network_gb,

    ai_tokens_million =
        EXCLUDED.ai_tokens_million,

    requests_count =
        EXCLUDED.requests_count,

    failed_requests =
        EXCLUDED.failed_requests,

    estimated_cost_usd =
        EXCLUDED.estimated_cost_usd,

    carbon_estimate_kg =
        EXCLUDED.carbon_estimate_kg,

    loaded_at =
        CURRENT_TIMESTAMP;