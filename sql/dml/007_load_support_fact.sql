INSERT INTO warehouse.fact_support_ticket (
    ticket_id,
    customer_key,
    product_key,
    opened_date_key,
    closed_date_key,
    severity,
    category,
    resolution_hours,
    sla_target_hours,
    sla_met,
    reopened,
    customer_satisfaction
)

SELECT
    s.ticket_id,
    c.customer_key,
    p.product_key,

    TO_CHAR(
        s.opened_date,
        'YYYYMMDD'
    )::INTEGER,

    CASE
        WHEN s.closed_date IS NULL
        THEN NULL

        ELSE TO_CHAR(
            s.closed_date,
            'YYYYMMDD'
        )::INTEGER
    END,

    s.severity,
    s.category,
    s.resolution_hours,
    s.sla_target_hours,
    s.sla_met,
    s.reopened,
    s.customer_satisfaction

FROM staging.support_tickets s

JOIN warehouse.dim_customer c
    ON c.customer_id =
       s.customer_id

LEFT JOIN warehouse.dim_product p
    ON p.product_code =
       s.product_code

ON CONFLICT (ticket_id)

DO UPDATE SET
    closed_date_key =
        EXCLUDED.closed_date_key,

    resolution_hours =
        EXCLUDED.resolution_hours,

    sla_met =
        EXCLUDED.sla_met,

    reopened =
        EXCLUDED.reopened,

    customer_satisfaction =
        EXCLUDED.customer_satisfaction;