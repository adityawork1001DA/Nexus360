INSERT INTO warehouse.dim_date (
    date_key,
    full_date,
    day_of_month,
    day_name,
    day_of_week,
    week_of_year,
    month_number,
    month_name,
    quarter_number,
    year_number,
    year_month,
    is_weekend,
    fiscal_year,
    fiscal_quarter
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER,

    d::DATE,

    EXTRACT(DAY FROM d)::SMALLINT,

    TO_CHAR(d, 'FMDay'),

    EXTRACT(ISODOW FROM d)::SMALLINT,

    EXTRACT(WEEK FROM d)::SMALLINT,

    EXTRACT(MONTH FROM d)::SMALLINT,

    TO_CHAR(d, 'FMMonth'),

    EXTRACT(QUARTER FROM d)::SMALLINT,

    EXTRACT(YEAR FROM d)::SMALLINT,

    TO_CHAR(d, 'YYYY-MM'),

    EXTRACT(ISODOW FROM d)
        IN (6, 7),

    EXTRACT(YEAR FROM d)::SMALLINT,

    EXTRACT(QUARTER FROM d)::SMALLINT

FROM GENERATE_SERIES(
    DATE '2018-01-01',
    DATE '2030-12-31',
    INTERVAL '1 day'
) AS dates(d)

ON CONFLICT (date_key)
DO NOTHING;