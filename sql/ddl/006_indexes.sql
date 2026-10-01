CREATE INDEX IF NOT EXISTS
idx_revenue_date
ON warehouse.fact_revenue(date_key);


CREATE INDEX IF NOT EXISTS
idx_revenue_customer
ON warehouse.fact_revenue(customer_key);


CREATE INDEX IF NOT EXISTS
idx_revenue_product
ON warehouse.fact_revenue(product_key);


CREATE INDEX IF NOT EXISTS
idx_revenue_region_date
ON warehouse.fact_revenue(
    region_key,
    date_key
);


CREATE INDEX IF NOT EXISTS
idx_usage_customer_date
ON warehouse.fact_cloud_usage(
    customer_key,
    date_key
);


CREATE INDEX IF NOT EXISTS
idx_usage_product_date
ON warehouse.fact_cloud_usage(
    product_key,
    date_key
);


CREATE INDEX IF NOT EXISTS
idx_ticket_customer
ON warehouse.fact_support_ticket(
    customer_key
);


CREATE INDEX IF NOT EXISTS
idx_ticket_opened_date
ON warehouse.fact_support_ticket(
    opened_date_key
);


CREATE INDEX IF NOT EXISTS
idx_churn_probability
ON ml.customer_churn_prediction(
    churn_probability DESC
);