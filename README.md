# Nexus360 — Enterprise Intelligence & Decision Automation Platform

Nexus360 is an end-to-end Enterprise Intelligence & Decision Automation Platform combining PostgreSQL data engineering, analytics, machine learning, a grounded AI copilot, Streamlit dashboards, Power BI Desktop, external APIs, automated pipelines, testing and cloud deployment.

## Architecture

```text
Enterprise + External Data
          |
         RAW
          |
       STAGING
          |
      WAREHOUSE
          |
      ANALYTICS
       /      \
   ML / AI     BI
      |       /  \
AI Copilot Streamlit Power BI
```

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| Database | PostgreSQL / Neon PostgreSQL |
| Database Access | SQLAlchemy + Psycopg |
| Data Processing | Pandas / NumPy |
| Machine Learning | Scikit-learn / XGBoost |
| Generative AI | Google Gemini |
| Application | Streamlit |
| Visualization | Plotly |
| BI | Microsoft Power BI Desktop |
| External Intelligence | World Bank, Open-Meteo, Frankfurter |
| Testing | Pytest |
| Version Control | Git + GitHub |

## Data Platform

Nexus360 follows a layered architecture:

- **RAW** — source-aligned enterprise and external data.
- **STAGING** — standardized data prepared for warehouse loading.
- **WAREHOUSE** — dimensional and fact-oriented analytical structures.
- **ANALYTICS** — business-ready semantic views consumed by dashboards and AI.

Warehouse dimensions cover customer, country, currency, datacenter, date, product, and region. Fact domains cover revenue, subscriptions, cloud usage, support, economic indicators, FX rates, and weather.

## Analytics

The SQL analytics layer includes executive KPIs, monthly and rolling revenue, YoY growth, regional performance, product ranking and penetration, Customer 360, Pareto/RFM/value tiers/cohorts, subscription health and renewal risk, AI adoption, Cloud FinOps, customer cloud efficiency, datacenter operations, sustainability, support SLA analytics, weather/cloud correlation, FX exposure, macroeconomic revenue, market opportunity, revenue anomalies, revenue at risk, and business health scoring.

## External Intelligence

Nexus360 integrates:

- **World Bank API** for macroeconomic indicators.
- **Open-Meteo Archive API** for historical weather intelligence.
- **Frankfurter API** for foreign-exchange data.

## Machine Learning

The project includes feature engineering, training dataset generation, model training, model persistence, and current churn prediction. Supporting scripts include `train_models.py`, `run_ml.py`, and `predict_current_churn.py`.

## Nexus360 AI Copilot

The Gemini-powered copilot uses a controlled semantic path:

```text
Question
  -> Intent Router
  -> Semantic Catalog
  -> Retriever
  -> Grounding Engine
  -> Context Builder
  -> Guardrails
  -> Gemini
  -> Grounded Business Answer
```

AI modules implement routing, retrieval, grounding, context construction, schemas, guardrails, configuration, and model access.

## Streamlit Application

Implemented application modules include Home, Executive, Customer, Revenue, Cloud Intelligence, Market, Product, Machine Learning, AI, and Admin.

The deployed application supports interactive analytics, business filtering, AI-assisted analysis, and administrative data operations.

## Power BI

The final Power BI Desktop dashboard is stored at:

```text
artifacts/powerbi/Nexus360_Enterprise_Dashboard.pbix
```

Power BI Desktop is the current BI authoring environment. Power BI Service is not required for the current release.

Future dashboard updates follow:

```text
Edit PBIX -> Save -> Git add -> Commit -> Push
```

## Incremental Pipeline

The end-to-end pipeline is orchestrated through `scripts/run_pipeline.py`.

```text
Incremental Generation
        |
       RAW
        |
     STAGING
        |
    WAREHOUSE
        |
    ANALYTICS
        |
 Dashboard + AI
```

The production incremental workflow has been successfully validated against the cloud PostgreSQL environment.

## Testing & Validation

Automated tests cover AI grounding, analytics, database schema, the enterprise warehouse, Excel reporting, external sources, external warehouse integration, ML features/modeling/pipelines/training datasets, Python analytics, and the Streamlit foundation.

Verified regression baseline:

```text
333 passed
```

Production validation also covered database connectivity, data propagation, Cloud Intelligence schema compatibility, AI grounding, dashboard operation, and incremental pipeline execution.

## Production Architecture

```text
                  GitHub
                     |
              Source Control
                     |
                     v
            Streamlit Application
               /            \
              v              v
      Neon PostgreSQL     Gemini API
              |
 RAW -> STAGING -> WAREHOUSE -> ANALYTICS
              |                    |
              v                    v
       Streamlit Analytics     Power BI Desktop
```

## Project Structure

```text
Nexus360/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- artifacts/
|   `-- powerbi/
|       `-- Nexus360_Enterprise_Dashboard.pbix
|-- config/
|-- data/
|-- docs/
|-- models/
|-- reports/
|-- scripts/
|-- sql/
|   |-- ddl/
|   |-- dml/
|   `-- analytics/
|-- src/
|   |-- ai/
|   |-- database/
|   `-- ui/
`-- tests/
```

## Local Setup

```powershell
git clone <repository-url>
cd Nexus360

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

Copy-Item .env.example .env
# Configure PostgreSQL and GEMINI_API_KEY in .env

$env:PYTHONPATH = (Get-Location).Path
streamlit run app.py
```

Never commit real credentials.

## Run Tests

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

Verified baseline: **333 passed**.

## Useful Utilities

```powershell
python scripts/check_raw_counts.py
python scripts/check_raw_integrity.py
python scripts/check_cloud_fact_integrity.py
python scripts/db_healthcheck.py
python scripts/ingest_external_data.py
```

## Security

- Secrets are loaded from environment variables.
- `.env` and Streamlit secrets are excluded from Git.
- Database and Gemini credentials are not hard-coded.
- Cloud PostgreSQL connectivity uses SSL.
- Local database backups are excluded from Git.
- AI requests pass through application-level grounding and guardrails.

## Release

The repository contains the **v1.0.0** production release tag. Documentation and artifact-organization commits may follow that release on `main`.

## Future Enhancements

Potential extensions include Power BI Service publishing, CI/CD, scheduled cloud orchestration, advanced model monitoring, additional external intelligence, expanded AI workflows, enterprise authentication, and production observability.

## Summary

Nexus360 demonstrates an integrated enterprise intelligence workflow:

**Data Engineering + Analytics Engineering + PostgreSQL + Machine Learning + Generative AI + Streamlit + Power BI + External APIs + Cloud Deployment + Automated Testing**
