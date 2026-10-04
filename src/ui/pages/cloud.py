from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.data_loader import AnalyticsDataLoader
from src.ui.components.cloud import (
    render_cloud_executive_insights,
    render_cloud_kpis,
    render_customer_efficiency_distribution,
    render_customer_efficiency_matrix,
    render_customer_optimization_table,
    render_datacenter_capacity,
    render_datacenter_reliability,
    render_datacenter_table,
    render_finops_efficiency_table,
    render_finops_unit_economics,
    render_product_cloud_cost,
    render_sustainability_matrix,
    render_sustainability_ranking,
    render_weather_correlation_detail,
    render_weather_correlations,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_cloud_intelligence_data() -> dict[str, pd.DataFrame]:

    loader = AnalyticsDataLoader()

    finops = loader.load_view(
        "v_cloud_finops"
    ).copy()

    customers = loader.load_view(
        "v_customer_cloud_efficiency"
    ).copy()

    datacenters = loader.load_view(
        "v_datacenter_operations"
    ).copy()

    sustainability = loader.load_view(
        "v_cloud_sustainability"
    ).copy()

    weather = loader.load_view(
        "v_weather_cloud_correlation"
    ).copy()

    # --------------------------------------------------------
    # Semantic compatibility layer
    # --------------------------------------------------------
    # Cloud Intelligence UI originally used earlier semantic
    # column names. Production analytics views expose newer,
    # explicit metric names. Normalize them here so the UI
    # remains decoupled from physical view naming.
    # --------------------------------------------------------

    finops = finops.rename(
        columns={
            "cost_per_compute_hour_usd":
                "cost_per_compute_hour",
            "cost_per_million_requests_usd":
                "cost_per_million_requests",
            "carbon_kg_per_compute_hour":
                "carbon_per_compute_hour_kg",
            "cloud_cost_rank":
                "cost_rank",
        }
    )

    customers = customers.rename(
        columns={
            "revenue_usd":
                "lifetime_revenue_usd",
            "cloud_cost_to_revenue_pct":
                "cloud_cost_pct_of_revenue",
            "efficiency_quintile":
                "cloud_efficiency_quintile",
        }
    )

    sustainability = sustainability.rename(
        columns={
            "carbon_kg_per_compute_hour":
                "carbon_per_compute_hour_kg",
            "renewable_energy_rank":
                "renewable_rank",
            "carbon_intensity_rank":
                "carbon_efficiency_rank",
        }
    )

    weather = weather.rename(
        columns={
            "temperature_compute_corr":
                "temperature_compute_correlation",
            "temperature_cost_corr":
                "temperature_cost_correlation",
            "temperature_carbon_corr":
                "temperature_carbon_correlation",
            "max_temperature_failure_corr":
                "max_temperature_failure_correlation",
            "precipitation_failure_corr":
                "precipitation_failure_correlation",
            "wind_failure_corr":
                "wind_failure_correlation",
        }
    )

    # --------------------------------------------------------
    # Region enrichment
    # --------------------------------------------------------
    # Datacenter operations is the canonical source for region.
    # Sustainability/weather are datacenter-grain datasets, so
    # enrich region_name through datacenter_code.
    # --------------------------------------------------------

    if (
        "datacenter_code" in datacenters.columns
        and "region_name" in datacenters.columns
    ):
        region_map = (
            datacenters[
                ["datacenter_code", "region_name"]
            ]
            .drop_duplicates(
                subset=["datacenter_code"]
            )
        )

        if (
            "datacenter_code" in sustainability.columns
            and "region_name"
            not in sustainability.columns
        ):
            sustainability = sustainability.merge(
                region_map,
                on="datacenter_code",
                how="left",
            )

        if (
            "datacenter_code" in weather.columns
            and "region_name" not in weather.columns
        ):
            weather = weather.merge(
                region_map,
                on="datacenter_code",
                how="left",
            )

    # --------------------------------------------------------
    # Sustainability business band
    # --------------------------------------------------------
    # Build a deterministic relative band from the two rankings
    # already calculated by the analytics semantic layer.
    # Lower rank values represent stronger relative performance.
    # --------------------------------------------------------

    if (
        "sustainability_band"
        not in sustainability.columns
        and "renewable_rank" in sustainability.columns
        and "carbon_efficiency_rank"
        in sustainability.columns
    ):
        score = (
            sustainability["renewable_rank"]
            + sustainability["carbon_efficiency_rank"]
        ) / 2.0

        if len(sustainability) >= 3:
            percentile = score.rank(
                method="average",
                pct=True,
                ascending=True,
            )

            sustainability[
                "sustainability_band"
            ] = pd.cut(
                percentile,
                bins=[
                    0.0,
                    1 / 3,
                    2 / 3,
                    1.0,
                ],
                labels=[
                    "Leading",
                    "Balanced",
                    "Needs Attention",
                ],
                include_lowest=True,
            ).astype(str)

        else:
            sustainability[
                "sustainability_band"
            ] = "Balanced"

    return {
        "finops": finops,
        "customers": customers,
        "datacenters": datacenters,
        "sustainability": sustainability,
        "weather": weather,
    }


# ============================================================
# FILTER HELPERS
# ============================================================

def _safe_options(
    dataframe: pd.DataFrame,
    column: str,
) -> list[str]:

    if column not in dataframe.columns:
        return []

    return sorted(
        dataframe[column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def _apply_filters(
    finops: pd.DataFrame,
    customers: pd.DataFrame,
    datacenters: pd.DataFrame,
    sustainability: pd.DataFrame,
    weather: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:

    st.sidebar.markdown(
        "### Cloud Intelligence Filters"
    )

    # --------------------------------------------------------
    # PRODUCT FAMILY
    # --------------------------------------------------------

    product_families = _safe_options(
        finops,
        "product_family",
    )

    selected_product_families = (
        st.sidebar.multiselect(
            "Product Family",
            product_families,
            default=product_families,
            key="cloud_product_family_filter",
        )
    )

    if product_families:
        finops = finops[
            finops["product_family"].isin(
                selected_product_families
            )
        ].copy()

    # --------------------------------------------------------
    # CUSTOMER SEGMENT
    # --------------------------------------------------------

    segments = _safe_options(
        customers,
        "customer_segment",
    )

    selected_segments = st.sidebar.multiselect(
        "Customer Segment",
        segments,
        default=segments,
        key="cloud_customer_segment_filter",
    )

    if segments:
        customers = customers[
            customers["customer_segment"].isin(
                selected_segments
            )
        ].copy()

    # --------------------------------------------------------
    # INDUSTRY
    # --------------------------------------------------------

    industries = _safe_options(
        customers,
        "industry",
    )

    selected_industries = st.sidebar.multiselect(
        "Industry",
        industries,
        default=industries,
        key="cloud_industry_filter",
    )

    if industries:
        customers = customers[
            customers["industry"].isin(
                selected_industries
            )
        ].copy()

    # --------------------------------------------------------
    # AI CUSTOMER
    # --------------------------------------------------------

    ai_customer_filter = st.sidebar.selectbox(
        "Customer AI Status",
        [
            "All Customers",
            "AI Customers",
            "Non-AI Customers",
        ],
        key="cloud_ai_customer_filter",
    )

    if (
        ai_customer_filter == "AI Customers"
        and "is_ai_customer" in customers.columns
    ):
        customers = customers[
            customers["is_ai_customer"]
        ].copy()

    elif (
        ai_customer_filter == "Non-AI Customers"
        and "is_ai_customer" in customers.columns
    ):
        customers = customers[
            ~customers["is_ai_customer"]
        ].copy()

    # --------------------------------------------------------
    # CLOUD EFFICIENCY BAND
    # --------------------------------------------------------

    efficiency_bands = _safe_options(
        customers,
        "cloud_efficiency_band",
    )

    selected_efficiency_bands = (
        st.sidebar.multiselect(
            "Cloud Efficiency Band",
            efficiency_bands,
            default=efficiency_bands,
            key="cloud_efficiency_band_filter",
        )
    )

    if efficiency_bands:
        customers = customers[
            customers["cloud_efficiency_band"].isin(
                selected_efficiency_bands
            )
        ].copy()

    # --------------------------------------------------------
    # REGION
    # --------------------------------------------------------

    regions = _safe_options(
        datacenters,
        "region_name",
    )

    selected_regions = st.sidebar.multiselect(
        "Data Center Region",
        regions,
        default=regions,
        key="cloud_region_filter",
    )

    if regions:
        datacenters = datacenters[
            datacenters["region_name"].isin(
                selected_regions
            )
        ].copy()

        sustainability = sustainability[
            sustainability["region_name"].isin(
                selected_regions
            )
        ].copy()

        weather = weather[
            weather["region_name"].isin(
                selected_regions
            )
        ].copy()

    # --------------------------------------------------------
    # DATA CENTER
    # --------------------------------------------------------

    datacenter_codes = _safe_options(
        datacenters,
        "datacenter_code",
    )

    selected_datacenters = (
        st.sidebar.multiselect(
            "Data Center",
            datacenter_codes,
            default=datacenter_codes,
            key="cloud_datacenter_filter",
        )
    )

    if datacenter_codes:

        datacenters = datacenters[
            datacenters["datacenter_code"].isin(
                selected_datacenters
            )
        ].copy()

        sustainability = sustainability[
            sustainability["datacenter_code"].isin(
                selected_datacenters
            )
        ].copy()

        weather = weather[
            weather["datacenter_code"].isin(
                selected_datacenters
            )
        ].copy()

    return (
        finops,
        customers,
        datacenters,
        sustainability,
        weather,
    )


# ============================================================
# DATA VALIDATION
# ============================================================

def _validate_bundle(
    bundle: dict[str, pd.DataFrame],
) -> bool:

    required = {
        "finops": [
            "product_code",
            "product_name",
            "product_family",
            "compute_hours",
            "requests_count",
            "failed_requests",
            "estimated_cost_usd",
            "request_failure_rate_pct",
            "cost_per_compute_hour",
            "cost_per_million_requests",
            "carbon_estimate_kg",
        ],
        "customers": [
            "customer_id",
            "customer_name",
            "customer_segment",
            "industry",
            "lifetime_revenue_usd",
            "cloud_cost_usd",
            "revenue_to_cloud_cost_ratio",
            "cloud_cost_pct_of_revenue",
            "cloud_efficiency_band",
        ],
        "datacenters": [
            "datacenter_code",
            "datacenter_name",
            "region_name",
            "capacity_mw",
            "renewable_energy_pct",
            "compute_hours",
            "requests_count",
            "request_failure_rate_pct",
            "estimated_cost_usd",
            "carbon_estimate_kg",
        ],
        "sustainability": [
            "datacenter_code",
            "datacenter_name",
            "region_name",
            "renewable_energy_pct",
            "compute_hours",
            "carbon_estimate_kg",
            "carbon_per_compute_hour_kg",
            "renewable_rank",
            "carbon_efficiency_rank",
            "sustainability_band",
        ],
        "weather": [
            "datacenter_code",
            "datacenter_name",
            "region_name",
            "observation_days",
        ],
    }

    errors: list[str] = []

    for dataset_name, columns in required.items():

        dataframe = bundle.get(
            dataset_name
        )

        if dataframe is None:
            errors.append(
                f"{dataset_name}: dataset missing"
            )
            continue

        missing = [
            column
            for column in columns
            if column not in dataframe.columns
        ]

        if missing:
            errors.append(
                f"{dataset_name}: missing columns "
                + ", ".join(missing)
            )

    if errors:

        st.error(
            "Cloud Intelligence schema validation failed."
        )

        for error in errors:
            st.write(f"- {error}")

        return False

    return True


# ============================================================
# PAGE
# ============================================================

def render() -> None:

    st.title(
        "Cloud, FinOps & Sustainability Intelligence"
    )

    st.caption(
        "Enterprise cloud economics, infrastructure operations, "
        "customer efficiency, sustainability and environmental analytics."
    )

    st.info(
        """
This command center connects five dimensions of cloud performance:

**FinOps**
- Where is infrastructure money being spent?
- Which products have the highest unit costs?

**Customer Economics**
- Which customers generate strong revenue relative to cloud cost?
- Where may optimization be valuable?

**Data Center Operations**
- How do workload, capacity and reliability differ across facilities?

**Sustainability**
- Which data centers combine renewable energy with lower carbon intensity?

**Environmental Intelligence**
- Are weather variables statistically associated with workload, cost,
  carbon emissions or request failures?

Use the sidebar to filter the analysis.
"""
    )

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    try:

        bundle = load_cloud_intelligence_data()

    except Exception as exc:

        st.error(
            "Unable to load Cloud Intelligence data."
        )

        st.exception(exc)

        return

    if not _validate_bundle(bundle):
        return

    finops = bundle["finops"]
    customers = bundle["customers"]
    datacenters = bundle["datacenters"]
    sustainability = bundle[
        "sustainability"
    ]
    weather = bundle["weather"]

    # --------------------------------------------------------
    # EMPTY DATA CHECK
    # --------------------------------------------------------

    empty_sources = [
        name
        for name, dataframe in bundle.items()
        if dataframe.empty
    ]

    if empty_sources:

        st.warning(
            "The following Cloud Intelligence datasets "
            "contain no records: "
            + ", ".join(empty_sources)
        )

        return

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    (
        finops,
        customers,
        datacenters,
        sustainability,
        weather,
    ) = _apply_filters(
        finops,
        customers,
        datacenters,
        sustainability,
        weather,
    )

    if (
        finops.empty
        or customers.empty
        or datacenters.empty
        or sustainability.empty
        or weather.empty
    ):

        st.warning(
            "No records match the current Cloud Intelligence filters."
        )

        return

    # --------------------------------------------------------
    # EXECUTIVE KPIs
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader(
        "Cloud Command Center"
    )

    st.caption(
        "High-level cloud economics, workload, reliability "
        "and sustainability indicators."
    )

    render_cloud_kpis(
        finops,
        datacenters,
    )

    st.markdown("---")

    # --------------------------------------------------------
    # TABS
    # --------------------------------------------------------

    (
        tab_finops,
        tab_customer,
        tab_operations,
        tab_sustainability,
        tab_weather,
        tab_insights,
    ) = st.tabs(
        [
            "FinOps",
            "Customer Efficiency",
            "Data Center Operations",
            "Sustainability",
            "Weather Intelligence",
            "Executive Insights",
        ]
    )

    # ========================================================
    # FINOPS
    # ========================================================

    with tab_finops:

        st.markdown(
            """
### FinOps Intelligence

FinOps connects engineering consumption with financial accountability.

Raw cloud spend alone does not tell us whether a workload is efficient.
For that reason, this section evaluates both **total cost** and
**unit economics**.
"""
        )

        render_product_cloud_cost(
            finops
        )

        st.markdown("---")

        render_finops_unit_economics(
            finops
        )

        st.markdown("---")

        render_finops_efficiency_table(
            finops
        )

    # ========================================================
    # CUSTOMER EFFICIENCY
    # ========================================================

    with tab_customer:

        st.markdown(
            """
### Customer Cloud Efficiency

This section connects customer commercial value with the infrastructure
required to serve that customer.

Two especially useful metrics are:

**Revenue-to-Cloud-Cost Ratio**

Higher values mean more revenue is generated relative to cloud cost.

**Cloud Cost % of Revenue**

Lower values generally indicate that cloud infrastructure consumes a
smaller proportion of customer revenue.

Neither metric should be treated as a complete profitability measure.
"""
        )

        render_customer_efficiency_distribution(
            customers
        )

        st.markdown("---")

        render_customer_efficiency_matrix(
            customers
        )

        st.markdown("---")

        render_customer_optimization_table(
            customers
        )

    # ========================================================
    # DATA CENTER OPERATIONS
    # ========================================================

    with tab_operations:

        st.markdown(
            """
### Data Center Operations

Infrastructure performance should be evaluated across several dimensions:

- capacity,
- workload,
- request volume,
- reliability,
- cost,
- renewable energy,
- carbon footprint.

The current warehouse does not yet contain a formal utilization
percentage, so capacity and compute workload are shown together without
claiming that their ratio represents physical utilization.
"""
        )

        render_datacenter_capacity(
            datacenters
        )

        st.markdown("---")

        render_datacenter_reliability(
            datacenters
        )

        st.markdown("---")

        render_datacenter_table(
            datacenters
        )

    # ========================================================
    # SUSTAINABILITY
    # ========================================================

    with tab_sustainability:

        st.markdown(
            """
### Cloud Sustainability

Total carbon emissions can increase simply because workload grows.

Therefore, this section evaluates both:

**Absolute Carbon Footprint**
- total estimated carbon emissions.

**Carbon Intensity**
- carbon emissions normalized by compute workload.

It also compares these metrics with renewable-energy percentage.
"""
        )

        render_sustainability_matrix(
            sustainability
        )

        st.markdown("---")

        render_sustainability_ranking(
            sustainability
        )

    # ========================================================
    # WEATHER
    # ========================================================

    with tab_weather:

        st.markdown(
            """
### Weather and Cloud Operations

This analysis explores statistical relationships between environmental
conditions and cloud operations.

The semantic layer currently provides correlations for:

- temperature vs compute,
- temperature vs cost,
- temperature vs carbon,
- maximum temperature vs failures,
- precipitation vs failures,
- wind vs failures.

A correlation is an analytical signal only. It does not establish
that weather caused the operational outcome.
"""
        )

        render_weather_correlations(
            weather
        )

        st.markdown("---")

        render_weather_correlation_detail(
            weather
        )

    # ========================================================
    # EXECUTIVE INSIGHTS
    # ========================================================

    with tab_insights:

        st.markdown(
            """
### Executive Decision Support

This section converts the current analytical results into a small number
of management signals.

The results remain descriptive rather than prescriptive. Human review is
required before infrastructure, pricing or customer decisions are made.
"""
        )

        render_cloud_executive_insights(
            finops,
            customers,
            datacenters,
            sustainability,
        )

    # ========================================================
    # METRIC DICTIONARY
    # ========================================================

    st.markdown("---")

    with st.expander(
        "Cloud Intelligence Metric Dictionary"
    ):

        st.markdown(
            """
### FinOps Metrics

**Estimated Cloud Cost**

Estimated infrastructure cost associated with a workload, product,
customer or data center.

**Cost per Compute Hour**

```text
Estimated Cloud Cost
--------------------
Compute Hours
```
"""
        )