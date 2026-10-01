INSERT INTO warehouse.dim_region (
    region_code,
    region_name,
    geography_group
)
VALUES

(
    'NAM',
    'North America',
    'AMER'
),

(
    'LATAM',
    'Latin America',
    'AMER'
),

(
    'WEU',
    'Western Europe',
    'EMEA'
),

(
    'NEU',
    'Northern Europe',
    'EMEA'
),

(
    'MEA',
    'Middle East & Africa',
    'EMEA'
),

(
    'IND',
    'India',
    'APAC'
),

(
    'SEA',
    'Southeast Asia',
    'APAC'
),

(
    'JPN',
    'Japan',
    'APAC'
),

(
    'ANZ',
    'Australia & New Zealand',
    'APAC'
)

ON CONFLICT (region_code)
DO NOTHING;


INSERT INTO warehouse.dim_currency (
    currency_code,
    currency_name,
    currency_symbol
)
VALUES
    ('USD', 'US Dollar', '$'),
    ('EUR', 'Euro', '€'),
    ('GBP', 'British Pound', '£'),
    ('INR', 'Indian Rupee', '₹'),
    ('JPY', 'Japanese Yen', '¥'),
    ('CAD', 'Canadian Dollar', 'C$'),
    ('AUD', 'Australian Dollar', 'A$'),
    ('SGD', 'Singapore Dollar', 'S$'),
    ('BRL', 'Brazilian Real', 'R$'),
    ('AED', 'UAE Dirham', 'د.إ')
ON CONFLICT (currency_code)
DO NOTHING;


INSERT INTO warehouse.dim_product (
    product_code,
    product_name,
    product_family,
    service_category,
    pricing_model,
    unit_of_measure,
    is_ai_service
)
VALUES

(
    'NC-COMPUTE',
    'Nexus Compute',
    'Cloud Infrastructure',
    'Compute',
    'Consumption',
    'Compute Hour',
    FALSE
),

(
    'NC-STORAGE',
    'Nexus Storage',
    'Cloud Infrastructure',
    'Storage',
    'Consumption',
    'GB-Month',
    FALSE
),

(
    'NC-SQL',
    'Nexus SQL Database',
    'Data Platform',
    'Database',
    'Consumption',
    'Compute Hour',
    FALSE
),

(
    'NC-WAREHOUSE',
    'Nexus Data Warehouse',
    'Data Platform',
    'Analytics',
    'Consumption',
    'Compute Unit',
    FALSE
),

(
    'NC-AIMODEL',
    'Nexus AI Models',
    'Artificial Intelligence',
    'Generative AI',
    'Consumption',
    'Million Tokens',
    TRUE
),

(
    'NC-AISEARCH',
    'Nexus AI Search',
    'Artificial Intelligence',
    'AI Search',
    'Consumption',
    '1000 Queries',
    TRUE
),

(
    'NC-SECURITY',
    'Nexus Cloud Security',
    'Security',
    'Cybersecurity',
    'Subscription',
    'Seat',
    FALSE
),

(
    'NC-ANALYTICS',
    'Nexus Analytics',
    'Data Platform',
    'Business Intelligence',
    'Subscription',
    'User',
    FALSE
),

(
    'NC-CONTAINER',
    'Nexus Container Platform',
    'Cloud Infrastructure',
    'Containers',
    'Consumption',
    'Node Hour',
    FALSE
),

(
    'NC-INTEGRATION',
    'Nexus Integration',
    'Application Platform',
    'Integration',
    'Consumption',
    '1000 Operations',
    FALSE
)

ON CONFLICT (product_code)
DO NOTHING;