# NEXUS 360 Data Dictionary

## warehouse.dim_customer

Enterprise customer master dimension.

### Grain

One row per enterprise customer.

### Primary Key

customer_key

### Business Key

customer_id

### Important Attributes

| Column | Description |
|---|---|
| customer_key | Warehouse surrogate key |
| customer_id | Source/business identifier |
| customer_name | Synthetic organization name |
| industry | Customer industry |
| customer_segment | SMB/Mid-Market/Enterprise/Strategic |
| country_key | Country FK |
| region_key | Region FK |
| signup_date | Customer acquisition date |
| customer_status | Current lifecycle status |
| is_ai_customer | Whether customer consumes AI products |