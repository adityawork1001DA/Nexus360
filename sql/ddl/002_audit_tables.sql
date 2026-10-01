CREATE TABLE IF NOT EXISTS audit.pipeline_run (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    pipeline_name VARCHAR(100) NOT NULL,

    source_name VARCHAR(100),

    status VARCHAR(20) NOT NULL
        CHECK (
            status IN (
                'STARTED',
                'SUCCESS',
                'FAILED',
                'PARTIAL'
            )
        ),

    started_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    rows_read BIGINT DEFAULT 0
        CHECK (rows_read >= 0),

    rows_inserted BIGINT DEFAULT 0
        CHECK (rows_inserted >= 0),

    rows_updated BIGINT DEFAULT 0
        CHECK (rows_updated >= 0),

    rows_rejected BIGINT DEFAULT 0
        CHECK (rows_rejected >= 0),

    error_message TEXT,

    metadata JSONB
);

CREATE TABLE IF NOT EXISTS audit.data_quality_result (
    quality_result_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    run_id BIGINT
        REFERENCES audit.pipeline_run(run_id),

    dataset_name VARCHAR(150) NOT NULL,

    rule_name VARCHAR(150) NOT NULL,

    rule_type VARCHAR(50),

    status VARCHAR(20) NOT NULL
        CHECK (
            status IN (
                'PASS',
                'WARN',
                'FAIL'
            )
        ),

    records_checked BIGINT,

    failed_records BIGINT,

    failure_percentage NUMERIC(8,4),

    details JSONB,

    checked_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);