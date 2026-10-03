from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticDomain:
    key: str
    label: str
    description: str
    views: tuple[str, ...]
    keywords: tuple[str, ...]


SEMANTIC_DOMAINS: dict[str, SemanticDomain] = {
    "executive": SemanticDomain(
        key="executive",
        label="Executive",
        description=(
            "Enterprise KPIs, business health, revenue, "
            "regional performance and commercial exposure."
        ),
        views=(
            "v_executive_kpis",
            "v_monthly_revenue",
            "v_regional_performance",
            "v_product_revenue_rank",
            "v_revenue_at_risk",
            "v_business_health_score",
        ),
        keywords=(
            "executive",
            "business performance",
            "business health",
            "kpi",
            "overall",
            "company performance",
            "management",
        ),
    ),
    "revenue": SemanticDomain(
        key="revenue",
        label="Revenue",
        description=(
            "Revenue trends, growth, geography, products, "
            "customers and commercial performance."
        ),
        views=(
            "v_monthly_revenue",
            "v_regional_performance",
            "v_product_revenue_rank",
            "v_customer_360",
            "v_revenue_at_risk",
        ),
        keywords=(
            "revenue",
            "sales",
            "growth",
            "arr",
            "mrr",
            "profit",
            "margin",
            "gross profit",
            "country",
            "region",
            "geography",
        ),
    ),
    "customer": SemanticDomain(
        key="customer",
        label="Customer",
        description=(
            "Customer 360, value segmentation, RFM, cohorts, "
            "retention, subscriptions and commercial risk."
        ),
        views=(
            "v_customer_360",
            "v_customer_rfm",
            "v_customer_pareto",
            "v_customer_value_tiers",
            "v_customer_cohort",
            "v_subscription_health",
            "v_subscription_renewal_risk",
            "v_revenue_at_risk",
        ),
        keywords=(
            "customer",
            "client",
            "account",
            "rfm",
            "segment",
            "cohort",
            "retention",
            "subscription",
            "renewal",
            "customer value",
            "pareto",
        ),
    ),
    "product": SemanticDomain(
        key="product",
        label="Product & AI",
        description=(
            "Product performance, product revenue, adoption "
            "and AI-related commercial intelligence."
        ),
        views=(
            "v_product_revenue_rank",
            "v_customer_360",
        ),
        keywords=(
            "product",
            "sku",
            "ai customer",
            "ai adoption",
            "product revenue",
            "product performance",
        ),
    ),
    "cloud": SemanticDomain(
        key="cloud",
        label="Cloud & FinOps",
        description=(
            "Cloud infrastructure economics, workload consumption, "
            "customer cloud efficiency, data-center operations, "
            "sustainability and weather-related operational intelligence."
        ),
        views=(
            "v_cloud_finops",
            "v_customer_cloud_efficiency",
            "v_datacenter_operations",
            "v_cloud_sustainability",
            "v_weather_cloud_correlation",
        ),
        keywords=(
            "cloud",
            "finops",
            "cloud cost",
            "cloud spend",
            "infrastructure cost",
            "compute",
            "compute hours",
            "storage",
            "storage gb",
            "network",
            "network gb",
            "usage",
            "workload",
            "requests",
            "failed requests",
            "failure rate",
            "unit economics",
            "cost efficiency",
            "cost per compute",
            "customer cloud efficiency",
            "datacenter",
            "data center",
            "capacity",
            "capacity mw",
            "renewable energy",
            "sustainability",
            "carbon",
            "carbon footprint",
            "emissions",
            "weather",
            "temperature",
        ),
    ),

        "market": SemanticDomain(
        key="market",
        label="Market Intelligence",
        description=(
            "Global market intelligence, foreign-exchange exposure, "
            "macroeconomic conditions, digital readiness, AI adoption, "
            "commercial whitespace and geographic market opportunity."
        ),
        views=(
            "v_fx_exposure",
            "v_macroeconomic_revenue",
            "v_market_opportunity",
        ),
        keywords=(
            "market",
            "markets",
            "market intelligence",
            "market opportunity",
            "market trends",
            "economic",
            "economic trends",
            "economy",
            "macroeconomic",
            "macroeconomic trends",
            "macro",
            "gdp",
            "gdp per capita",
            "inflation",
            "internet usage",
            "digital readiness",
            "market whitespace",
            "commercial whitespace",
            "exchange rate",
            "exchange rates",
            "foreign exchange",
            "fx",
            "fx exposure",
            "fx risk",
            "currency",
            "currency exposure",
            "currency risk",
            "world bank",
        ),
    ),
    "support": SemanticDomain(
        key="support",
        label="Support",
        description=(
            "Customer support workload, SLA performance, "
            "ticket reopening and service quality."
        ),
        views=(
            "v_customer_360",
        ),
        keywords=(
            "support",
            "ticket",
            "sla",
            "resolution",
            "reopened",
            "service quality",
            "customer satisfaction",
        ),
    ),
    "ml": SemanticDomain(
        key="ml",
        label="Predictive ML",
        description=(
            "Current churn risk, customer risk ranking, "
            "historical model performance and model drivers."
        ),
        views=(),
        keywords=(
            "churn",
            "risk probability",
            "prediction",
            "predictive",
            "machine learning",
            "model",
            "roc",
            "auc",
            "precision",
            "recall",
            "feature importance",
            "at risk",
        ),
    ),
}


DOMAIN_ALIASES: dict[str, str] = {
    "predictive ml": "ml",
    "machine learning": "ml",
    "churn": "ml",
    "customers": "customer",
    "customer intelligence": "customer",
    "revenue intelligence": "revenue",
    "product intelligence": "product",
    "finops": "cloud",
    "cloud finops": "cloud",
    "market intelligence": "market",
    "economic intelligence": "market",
    "macroeconomic intelligence": "market",
    "fx": "market",
}


def get_domain(
    key: str,
) -> SemanticDomain:
    cleaned = str(key).strip().lower()

    cleaned = DOMAIN_ALIASES.get(
        cleaned,
        cleaned,
    )

    return SEMANTIC_DOMAINS.get(
        cleaned,
        SEMANTIC_DOMAINS["executive"],
    )