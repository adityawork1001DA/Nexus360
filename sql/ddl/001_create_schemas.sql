BEGIN;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS audit;

COMMENT ON SCHEMA raw IS
'Raw source data loaded with minimal transformation.';

COMMENT ON SCHEMA staging IS
'Cleaned, standardized and validated source data.';

COMMENT ON SCHEMA warehouse IS
'Dimensional enterprise data warehouse.';

COMMENT ON SCHEMA analytics IS
'Business-facing analytical views and marts.';

COMMENT ON SCHEMA ml IS
'Machine-learning features, predictions and monitoring.';

COMMENT ON SCHEMA audit IS
'Pipeline execution, data quality and operational metadata.';

COMMIT;