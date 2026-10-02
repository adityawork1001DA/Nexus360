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



INSERT INTO warehouse.dim_datacenter (
    datacenter_code,
    datacenter_name,
    city,
    region_key,
    latitude,
    longitude,
    capacity_mw,
    renewable_energy_pct,
    operational_since
)
SELECT
    v.datacenter_code,
    v.datacenter_name,
    v.city,
    r.region_key,
    v.latitude,
    v.longitude,
    v.capacity_mw,
    v.renewable_pct,
    v.operational_since
FROM (
    VALUES

    (
        'DC-US-EAST',
        'Nexus US East',
        'Virginia',
        'NAM',
        37.4316,
        -78.6569,
        180.00,
        72.00,
        DATE '2018-01-01'
    ),

    (
        'DC-US-WEST',
        'Nexus US West',
        'Washington',
        'NAM',
        47.4009,
        -121.4905,
        160.00,
        86.00,
        DATE '2019-01-01'
    ),

    (
        'DC-EU-WEST',
        'Nexus Europe West',
        'Dublin',
        'WEU',
        53.3498,
        -6.2603,
        145.00,
        81.00,
        DATE '2019-06-01'
    ),

    (
        'DC-IND-CENTRAL',
        'Nexus India Central',
        'Pune',
        'IND',
        18.5204,
        73.8567,
        130.00,
        67.00,
        DATE '2020-01-01'
    ),

    (
        'DC-SEA',
        'Nexus Southeast Asia',
        'Singapore',
        'SEA',
        1.3521,
        103.8198,
        120.00,
        58.00,
        DATE '2020-06-01'
    ),

    (
        'DC-JPN',
        'Nexus Japan',
        'Tokyo',
        'JPN',
        35.6762,
        139.6503,
        115.00,
        62.00,
        DATE '2021-01-01'
    ),

    (
        'DC-ANZ',
        'Nexus Australia',
        'Sydney',
        'ANZ',
        -33.8688,
        151.2093,
        110.00,
        78.00,
        DATE '2021-06-01'
    )

) AS v(
    datacenter_code,
    datacenter_name,
    city,
    region_code,
    latitude,
    longitude,
    capacity_mw,
    renewable_pct,
    operational_since
)

JOIN warehouse.dim_region r
    ON r.region_code = v.region_code

ON CONFLICT (datacenter_code)
DO NOTHING;