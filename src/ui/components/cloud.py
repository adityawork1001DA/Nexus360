from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# FORMATTING
# ============================================================

def money(value: float | int | None) -> str:
    value = float(value or 0)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.2f}K"

    return f"${value:,.2f}"


def number(value: float | int | None) -> str:
    value = float(value or 0)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"

    return f"{value:,.0f}"


def decimal(value: float | int | None, digits: int = 2) -> str:
    return f"{float(value or 0):,.{digits}f}"


def pct(value: float | int | None) -> str:
    return f"{float(value or 0):,.2f}%"


def safe_divide(
    numerator: float,
    denominator: float,
    multiplier: float = 1.0,
) -> float:
    if denominator is None or float(denominator) == 0:
        return 0.0

    return float(numerator) / float(denominator) * multiplier


# ============================================================
# EXPLANATION COMPONENTS
# ============================================================

def section_explainer(
    title: str,
    definition: str,
    interpretation: str,
    business_use: str,
    caution: str | None = None,
) -> None:

    with st.expander(f"Understanding {title}"):

        st.markdown(
            f"""
**What it means**

{definition}

**How to interpret it**

{interpretation}

**Why it matters**

{business_use}
"""
        )

        if caution:
            st.warning(caution)


def correlation_strength(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "Unavailable"

    magnitude = abs(float(value))

    if magnitude < 0.10:
        return "Very weak"

    if magnitude < 0.30:
        return "Weak"

    if magnitude < 0.50:
        return "Moderate"

    if magnitude < 0.70:
        return "Strong"

    return "Very strong"


def correlation_direction(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "Unavailable"

    if value > 0:
        return "Positive"

    if value < 0:
        return "Negative"

    return "Neutral"


# ============================================================
# EXECUTIVE CLOUD KPIs
# ============================================================

def render_cloud_kpis(
    finops: pd.DataFrame,
    datacenters: pd.DataFrame,
) -> None:

    total_cost = finops["estimated_cost_usd"].sum()
    total_compute = finops["compute_hours"].sum()
    total_requests = finops["requests_count"].sum()
    total_failed = finops["failed_requests"].sum()
    total_carbon = finops["carbon_estimate_kg"].sum()

    failure_rate = safe_divide(
        total_failed,
        total_requests,
        100,
    )

    if not datacenters.empty:
        total_capacity = datacenters["capacity_mw"].sum()

        weighted_renewable = safe_divide(
            (
                datacenters["renewable_energy_pct"]
                * datacenters["capacity_mw"]
            ).sum(),
            total_capacity,
        )
    else:
        total_capacity = 0
        weighted_renewable = 0

    row1 = st.columns(4)

    row1[0].metric(
        "Cloud Spend",
        money(total_cost),
    )

    row1[1].metric(
        "Compute Hours",
        number(total_compute),
    )

    row1[2].metric(
        "Requests",
        number(total_requests),
    )

    row1[3].metric(
        "Request Failure Rate",
        pct(failure_rate),
    )

    row2 = st.columns(3)

    row2[0].metric(
        "Carbon Footprint",
        f"{number(total_carbon)} kg",
    )

    row2[1].metric(
        "Data Center Capacity",
        f"{number(total_capacity)} MW",
    )

    row2[2].metric(
        "Capacity-Weighted Renewable Energy",
        pct(weighted_renewable),
    )

    section_explainer(
        "Cloud Command Center KPIs",
        (
            "Cloud Spend measures estimated infrastructure cost. Compute Hours "
            "represent consumed compute workload. Requests measure platform "
            "activity. Request Failure Rate measures failed requests as a "
            "percentage of total requests. Carbon Footprint represents estimated "
            "cloud-related emissions. Renewable Energy measures the renewable "
            "share of data-center energy capacity."
        ),
        (
            "These metrics should be interpreted together. Growing cloud spend "
            "can be healthy when workload and revenue are growing proportionally. "
            "Rising spend without corresponding business or workload growth may "
            "indicate an optimization opportunity."
        ),
        (
            "The KPI layer gives engineering, FinOps, finance and sustainability "
            "leaders one shared operational view instead of evaluating cost, "
            "reliability and environmental impact separately."
        ),
    )


# ============================================================
# FINOPS
# ============================================================

def render_product_cloud_cost(finops: pd.DataFrame) -> None:

    st.subheader("Cloud Cost by Product")

    data = finops.sort_values(
        "estimated_cost_usd",
        ascending=True,
    ).copy()

    fig = px.bar(
        data,
        x="estimated_cost_usd",
        y="product_name",
        orientation="h",
        text="cost_rank",
        hover_data={
            "product_code": True,
            "product_family": True,
            "compute_hours": ":,.2f",
            "storage_gb": ":,.2f",
            "network_gb": ":,.2f",
            "requests_count": ":,",
            "request_failure_rate_pct": ":.4f",
            "carbon_estimate_kg": ":,.2f",
            "cost_per_compute_hour": ":.6f",
            "cost_per_million_requests": ":,.2f",
        },
        labels={
            "estimated_cost_usd": "Estimated Cloud Cost (USD)",
            "product_name": "Product",
        },
    )

    fig.update_traces(
        texttemplate="Rank %{text}",
        textposition="outside",
    )

    fig.update_layout(
        height=max(440, len(data) * 48),
        yaxis_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Cloud Cost by Product",
        (
            "This chart ranks products according to estimated cloud "
            "infrastructure cost."
        ),
        (
            "A high-cost product is not automatically inefficient. Products with "
            "high workload, high customer usage or high revenue may naturally "
            "consume more infrastructure."
        ),
        (
            "FinOps teams use this view to determine where deeper unit-economics "
            "analysis should be performed before making optimization decisions."
        ),
    )


def render_finops_unit_economics(finops: pd.DataFrame) -> None:

    st.subheader("Cloud Unit Economics")

    data = finops.copy()

    fig = px.scatter(
        data,
        x="cost_per_compute_hour",
        y="cost_per_million_requests",
        size="estimated_cost_usd",
        hover_name="product_name",
        hover_data={
            "product_family": True,
            "estimated_cost_usd": ":,.2f",
            "compute_hours": ":,.2f",
            "requests_count": ":,",
            "request_failure_rate_pct": ":.4f",
            "carbon_per_compute_hour_kg": ":.6f",
        },
        labels={
            "cost_per_compute_hour": "Cost per Compute Hour",
            "cost_per_million_requests": "Cost per Million Requests",
        },
    )

    if not data.empty:
        fig.add_vline(
            x=data["cost_per_compute_hour"].median(),
            line_dash="dash",
        )

        fig.add_hline(
            y=data["cost_per_million_requests"].median(),
            line_dash="dash",
        )

    fig.update_layout(height=520)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Cloud Unit Economics",
        (
            "Cost per Compute Hour measures infrastructure cost relative to "
            "compute consumption. Cost per Million Requests measures the cost "
            "required to serve one million requests."
        ),
        (
            "Products in the upper-right portion have relatively high values on "
            "both unit-cost measures and deserve investigation. Products in the "
            "lower-left are comparatively efficient on both measures."
        ),
        (
            "Unit economics normalize raw spend for workload and are therefore "
            "more useful than cost alone when comparing products with different "
            "usage volumes."
        ),
        caution=(
            "A high unit cost is an investigation signal, not proof of waste. "
            "Architecture, SLA requirements, workload complexity and product "
            "pricing can all affect unit economics."
        ),
    )


def render_finops_efficiency_table(finops: pd.DataFrame) -> None:

    st.subheader("FinOps Product Detail")

    columns = [
        "cost_rank",
        "product_code",
        "product_name",
        "product_family",
        "compute_hours",
        "storage_gb",
        "network_gb",
        "ai_tokens_million",
        "requests_count",
        "failed_requests",
        "request_failure_rate_pct",
        "estimated_cost_usd",
        "cost_per_compute_hour",
        "cost_per_million_requests",
        "carbon_estimate_kg",
        "carbon_per_compute_hour_kg",
    ]

    data = finops[
        [column for column in columns if column in finops.columns]
    ].sort_values("cost_rank")

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "estimated_cost_usd": st.column_config.NumberColumn(
                "Cloud Cost",
                format="$%.2f",
            ),
            "request_failure_rate_pct": st.column_config.NumberColumn(
                "Failure Rate",
                format="%.4f%%",
            ),
            "cost_per_compute_hour": st.column_config.NumberColumn(
                "Cost / Compute Hour",
                format="$%.6f",
            ),
            "cost_per_million_requests": st.column_config.NumberColumn(
                "Cost / 1M Requests",
                format="$%.2f",
            ),
            "carbon_estimate_kg": st.column_config.NumberColumn(
                "Carbon (kg)",
                format="%.2f",
            ),
        },
    )


# ============================================================
# CUSTOMER CLOUD EFFICIENCY
# ============================================================

def render_customer_efficiency_distribution(
    customers: pd.DataFrame,
) -> None:

    st.subheader("Customer Cloud Efficiency Distribution")

    data = (
        customers.groupby(
            "cloud_efficiency_band",
            as_index=False,
        )
        .agg(
            customers=("customer_id", "nunique"),
            lifetime_revenue_usd=(
                "lifetime_revenue_usd",
                "sum",
            ),
            cloud_cost_usd=(
                "cloud_cost_usd",
                "sum",
            ),
        )
    )

    fig = px.bar(
        data,
        x="cloud_efficiency_band",
        y="customers",
        text="customers",
        hover_data={
            "lifetime_revenue_usd": ":,.2f",
            "cloud_cost_usd": ":,.2f",
        },
        labels={
            "cloud_efficiency_band": "Efficiency Band",
            "customers": "Customers",
        },
    )

    fig.update_traces(
        textposition="outside",
    )

    fig.update_layout(height=440)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Customer Cloud Efficiency",
        (
            "Customer Cloud Efficiency compares customer commercial value with "
            "the cloud infrastructure cost associated with serving that customer."
        ),
        (
            "Efficiency bands provide a relative segmentation of customers. "
            "Customers in weaker efficiency bands can be reviewed for workload "
            "optimization, pricing alignment, architecture changes or commercial "
            "strategy."
        ),
        (
            "This connects infrastructure economics to customer economics, "
            "allowing FinOps analysis to move beyond product-level cost totals."
        ),
    )


def render_customer_efficiency_matrix(
    customers: pd.DataFrame,
) -> None:

    st.subheader("Customer Revenue vs Cloud Cost")

    data = customers.copy()

    fig = px.scatter(
        data,
        x="cloud_cost_usd",
        y="lifetime_revenue_usd",
        size="requests_count",
        hover_name="customer_name",
        hover_data={
            "customer_id": True,
            "customer_segment": True,
            "industry": True,
            "is_ai_customer": True,
            "revenue_to_cloud_cost_ratio": ":.2f",
            "cloud_cost_pct_of_revenue": ":.2f",
            "request_failure_rate_pct": ":.4f",
            "cloud_efficiency_band": True,
        },
        labels={
            "cloud_cost_usd": "Cloud Cost (USD)",
            "lifetime_revenue_usd": "Lifetime Revenue (USD)",
        },
    )

    fig.update_layout(height=560)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Customer Revenue vs Cloud Cost",
        (
            "The matrix compares the infrastructure cost associated with a "
            "customer against that customer's lifetime revenue."
        ),
        (
            "Customers generating substantial revenue relative to their cloud "
            "cost have stronger infrastructure economics. Customers with high "
            "cost and comparatively low revenue may deserve deeper analysis."
        ),
        (
            "Account, finance and cloud teams can use this view together when "
            "prioritizing optimization or pricing discussions."
        ),
    )


def render_customer_optimization_table(
    customers: pd.DataFrame,
) -> None:

    st.subheader("Customer Optimization Explorer")

    data = customers.copy()

    data = data.sort_values(
        [
            "cloud_cost_pct_of_revenue",
            "cloud_cost_usd",
        ],
        ascending=[False, False],
    )

    columns = [
        "customer_id",
        "customer_name",
        "customer_segment",
        "industry",
        "is_ai_customer",
        "lifetime_revenue_usd",
        "cloud_cost_usd",
        "revenue_to_cloud_cost_ratio",
        "cloud_cost_pct_of_revenue",
        "request_failure_rate_pct",
        "carbon_estimate_kg",
        "cloud_efficiency_quintile",
        "cloud_efficiency_band",
    ]

    st.dataframe(
        data[
            [column for column in columns if column in data.columns]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "lifetime_revenue_usd": st.column_config.NumberColumn(
                "Lifetime Revenue",
                format="$%.2f",
            ),
            "cloud_cost_usd": st.column_config.NumberColumn(
                "Cloud Cost",
                format="$%.2f",
            ),
            "revenue_to_cloud_cost_ratio": st.column_config.NumberColumn(
                "Revenue / Cloud Cost",
                format="%.2f",
            ),
            "cloud_cost_pct_of_revenue": st.column_config.ProgressColumn(
                "Cloud Cost % Revenue",
                min_value=0,
                max_value=max(
                    100.0,
                    float(
                        data["cloud_cost_pct_of_revenue"].max()
                        if not data.empty
                        else 100
                    ),
                ),
                format="%.2f%%",
            ),
            "request_failure_rate_pct": st.column_config.NumberColumn(
                "Failure Rate",
                format="%.4f%%",
            ),
        },
    )

    section_explainer(
        "Customer Optimization Explorer",
        (
            "Cloud Cost % of Revenue measures how much infrastructure cost is "
            "associated with each dollar of customer revenue. Revenue-to-Cloud-"
            "Cost Ratio expresses the relationship in the opposite direction."
        ),
        (
            "Higher cloud-cost percentages and lower revenue-to-cost ratios can "
            "signal weaker infrastructure economics."
        ),
        (
            "The table can help prioritize customers for technical optimization, "
            "commercial review or architecture assessment."
        ),
        caution=(
            "Do not automatically classify high-cost customers as unprofitable. "
            "This view does not include every possible customer-level operating "
            "expense or strategic consideration."
        ),
    )


# ============================================================
# DATA CENTER OPERATIONS
# ============================================================

def render_datacenter_capacity(datacenters: pd.DataFrame) -> None:

    st.subheader("Data Center Capacity and Workload")

    data = datacenters.copy()

    fig = px.scatter(
        data,
        x="capacity_mw",
        y="compute_hours",
        size="estimated_cost_usd",
        hover_name="datacenter_name",
        hover_data={
            "datacenter_code": True,
            "city": True,
            "region_code": True,
            "region_name": True,
            "renewable_energy_pct": ":.2f",
            "requests_count": ":,",
            "request_failure_rate_pct": ":.4f",
            "carbon_estimate_kg": ":,.2f",
        },
        labels={
            "capacity_mw": "Capacity (MW)",
            "compute_hours": "Compute Hours",
        },
    )

    fig.update_layout(height=520)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Data Center Capacity and Workload",
        (
            "Capacity MW represents available data-center power capacity, while "
            "Compute Hours represent workload processed by each facility."
        ),
        (
            "Comparing workload against capacity helps reveal differences in "
            "infrastructure utilization. The chart is directional because this "
            "semantic view does not expose a formal capacity-utilization KPI."
        ),
        (
            "Infrastructure teams can compare facilities and identify locations "
            "that deserve deeper capacity planning or workload-placement analysis."
        ),
    )


def render_datacenter_reliability(datacenters: pd.DataFrame) -> None:

    st.subheader("Data Center Reliability")

    data = datacenters.sort_values(
        "request_failure_rate_pct",
        ascending=False,
    ).copy()

    fig = px.bar(
        data,
        x="datacenter_name",
        y="request_failure_rate_pct",
        text="request_failure_rate_pct",
        hover_data={
            "datacenter_code": True,
            "city": True,
            "region_name": True,
            "requests_count": ":,",
            "failed_requests": ":,",
            "estimated_cost_usd": ":,.2f",
        },
        labels={
            "datacenter_name": "Data Center",
            "request_failure_rate_pct": "Request Failure Rate (%)",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.4f}%",
        textposition="outside",
    )

    fig.update_layout(
        height=460,
        xaxis_tickangle=-25,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Data Center Reliability",
        (
            "Request Failure Rate measures the percentage of requests that failed "
            "for workloads associated with each data center."
        ),
        (
            "Lower values generally indicate stronger request-level reliability. "
            "Small differences should still be evaluated against workload type, "
            "traffic volume and operational context."
        ),
        (
            "Operations teams can use this ranking to prioritize reliability "
            "investigation and compare infrastructure performance."
        ),
    )


def render_datacenter_table(datacenters: pd.DataFrame) -> None:

    st.subheader("Data Center Operations Detail")

    columns = [
        "datacenter_code",
        "datacenter_name",
        "city",
        "country_code",
        "country_name",
        "region_code",
        "region_name",
        "capacity_mw",
        "renewable_energy_pct",
        "compute_hours",
        "storage_gb",
        "network_gb",
        "requests_count",
        "failed_requests",
        "request_failure_rate_pct",
        "estimated_cost_usd",
        "carbon_estimate_kg",
    ]

    data = datacenters[
        [column for column in columns if column in datacenters.columns]
    ].copy()

    # Do not display country fields when the warehouse currently
    # contains no meaningful country mapping.
    for country_column in ["country_code", "country_name"]:
        if country_column in data.columns:
            meaningful = (
                data[country_column]
                .dropna()
                .astype(str)
                .str.strip()
            )

            meaningful = meaningful[
                ~meaningful.str.lower().isin(
                    {"", "unknown", "unk", "none", "nan"}
                )
            ]

            if meaningful.empty:
                data = data.drop(
                    columns=[country_column]
                )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "capacity_mw": st.column_config.NumberColumn(
                "Capacity MW",
                format="%.2f",
            ),
            "renewable_energy_pct": st.column_config.ProgressColumn(
                "Renewable Energy",
                min_value=0,
                max_value=100,
                format="%.2f%%",
            ),
            "request_failure_rate_pct": st.column_config.NumberColumn(
                "Failure Rate",
                format="%.4f%%",
            ),
            "estimated_cost_usd": st.column_config.NumberColumn(
                "Cloud Cost",
                format="$%.2f",
            ),
            "carbon_estimate_kg": st.column_config.NumberColumn(
                "Carbon kg",
                format="%.2f",
            ),
        },
    )


# ============================================================
# SUSTAINABILITY
# ============================================================

def render_sustainability_matrix(
    sustainability: pd.DataFrame,
) -> None:

    st.subheader("Renewable Energy vs Carbon Intensity")

    data = sustainability.copy()

    fig = px.scatter(
        data,
        x="renewable_energy_pct",
        y="carbon_per_compute_hour_kg",
        size="compute_hours",
        hover_name="datacenter_name",
        hover_data={
            "datacenter_code": True,
            "city": True,
            "region_name": True,
            "carbon_estimate_kg": ":,.2f",
            "estimated_cost_usd": ":,.2f",
            "renewable_rank": True,
            "carbon_efficiency_rank": True,
            "sustainability_band": True,
        },
        labels={
            "renewable_energy_pct": "Renewable Energy (%)",
            "carbon_per_compute_hour_kg": (
                "Carbon per Compute Hour (kg)"
            ),
        },
    )

    if not data.empty:
        fig.add_vline(
            x=data["renewable_energy_pct"].median(),
            line_dash="dash",
        )

        fig.add_hline(
            y=data["carbon_per_compute_hour_kg"].median(),
            line_dash="dash",
        )

    fig.update_layout(height=540)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Renewable Energy vs Carbon Intensity",
        (
            "Renewable Energy % measures the renewable share associated with a "
            "data center. Carbon per Compute Hour normalizes estimated emissions "
            "by compute workload."
        ),
        (
            "A desirable directional position is toward higher renewable-energy "
            "share and lower carbon intensity."
        ),
        (
            "The comparison supports sustainable workload placement, "
            "infrastructure planning and environmental performance analysis."
        ),
    )


def render_sustainability_ranking(
    sustainability: pd.DataFrame,
) -> None:

    st.subheader("Sustainability Ranking")

    data = sustainability.sort_values(
        [
            "carbon_efficiency_rank",
            "renewable_rank",
        ]
    ).copy()

    columns = [
        "datacenter_code",
        "datacenter_name",
        "city",
        "region_name",
        "capacity_mw",
        "renewable_energy_pct",
        "compute_hours",
        "estimated_cost_usd",
        "carbon_estimate_kg",
        "carbon_per_compute_hour_kg",
        "renewable_rank",
        "carbon_efficiency_rank",
        "sustainability_band",
    ]

    st.dataframe(
        data[
            [column for column in columns if column in data.columns]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "renewable_energy_pct": st.column_config.ProgressColumn(
                "Renewable Energy",
                min_value=0,
                max_value=100,
                format="%.2f%%",
            ),
            "estimated_cost_usd": st.column_config.NumberColumn(
                "Cloud Cost",
                format="$%.2f",
            ),
            "carbon_estimate_kg": st.column_config.NumberColumn(
                "Carbon kg",
                format="%.2f",
            ),
            "carbon_per_compute_hour_kg": (
                st.column_config.NumberColumn(
                    "Carbon / Compute Hour",
                    format="%.6f",
                )
            ),
        },
    )


# ============================================================
# WEATHER / CLOUD CORRELATION
# ============================================================

def render_weather_correlations(
    weather: pd.DataFrame,
) -> None:

    st.subheader("Weather Impact Correlation Matrix")

    metrics = {
        "temperature_compute_correlation": (
            "Temperature vs Compute"
        ),
        "temperature_cost_correlation": (
            "Temperature vs Cost"
        ),
        "temperature_carbon_correlation": (
            "Temperature vs Carbon"
        ),
        "max_temperature_failure_correlation": (
            "Max Temperature vs Failures"
        ),
        "precipitation_failure_correlation": (
            "Precipitation vs Failures"
        ),
        "wind_failure_correlation": (
            "Wind vs Failures"
        ),
    }

    available_metrics = [
        column
        for column in metrics
        if column in weather.columns
    ]

    if not available_metrics:
        st.info(
            "No weather correlation metrics are available."
        )
        return

    heatmap = weather.set_index(
        "datacenter_name"
    )[available_metrics].copy()

    heatmap = heatmap.rename(
        columns=metrics
    )

    fig = px.imshow(
        heatmap,
        text_auto=True,
        aspect="auto",
        zmin=-1,
        zmax=1,
        labels={
            "x": "Relationship",
            "y": "Data Center",
            "color": "Correlation",
        },
    )

    fig.update_layout(
        height=max(
            450,
            len(heatmap) * 65,
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Weather Correlation Matrix",
        (
            "Correlation measures the statistical direction and strength of a "
            "relationship between two variables. Values range from -1 to +1."
        ),
        (
            "Positive values mean the variables tended to move in the same "
            "direction. Negative values mean they tended to move in opposite "
            "directions. Values close to zero indicate weak linear association."
        ),
        (
            "This can help infrastructure teams identify environmental "
            "relationships worth deeper operational investigation."
        ),
        caution=(
            "Correlation does not prove causation. Weather correlation should "
            "not be interpreted as evidence that weather directly caused cloud "
            "cost, workload, carbon emissions or request failures."
        ),
    )


def render_weather_correlation_detail(
    weather: pd.DataFrame,
) -> None:

    st.subheader("Correlation Interpretation")

    metrics = {
        "temperature_compute_correlation": (
            "Temperature vs Compute"
        ),
        "temperature_cost_correlation": (
            "Temperature vs Cost"
        ),
        "temperature_carbon_correlation": (
            "Temperature vs Carbon"
        ),
        "max_temperature_failure_correlation": (
            "Max Temperature vs Failures"
        ),
        "precipitation_failure_correlation": (
            "Precipitation vs Failures"
        ),
        "wind_failure_correlation": (
            "Wind vs Failures"
        ),
    }

    records: list[dict] = []

    for _, row in weather.iterrows():

        for column, label in metrics.items():

            if column not in weather.columns:
                continue

            value = row[column]

            records.append(
                {
                    "Data Center": row[
                        "datacenter_name"
                    ],
                    "Relationship": label,
                    "Correlation": value,
                    "Direction": correlation_direction(
                        value
                    ),
                    "Strength": correlation_strength(
                        value
                    ),
                    "Observations": row.get(
                        "observation_days",
                        np.nan,
                    ),
                }
            )

    detail = pd.DataFrame(records)

    if detail.empty:
        st.info(
            "No correlation details available."
        )
        return

    detail["Absolute Correlation"] = (
        detail["Correlation"].abs()
    )

    detail = detail.sort_values(
        "Absolute Correlation",
        ascending=False,
    ).drop(
        columns=["Absolute Correlation"]
    )

    st.dataframe(
        detail,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Correlation": st.column_config.NumberColumn(
                "Correlation",
                format="%.4f",
            ),
            "Observations": st.column_config.NumberColumn(
                "Observation Days",
                format="%d",
            ),
        },
    )


# ============================================================
# EXECUTIVE INSIGHTS
# ============================================================

def render_cloud_executive_insights(
    finops: pd.DataFrame,
    customers: pd.DataFrame,
    datacenters: pd.DataFrame,
    sustainability: pd.DataFrame,
) -> None:

    st.subheader("Executive Cloud Insights")

    if finops.empty:
        st.info("No FinOps data available.")
        return

    highest_cost_product = finops.iloc[
        finops["estimated_cost_usd"].argmax()
    ]

    highest_unit_cost = finops.iloc[
        finops["cost_per_compute_hour"].argmax()
    ]

    highest_failure_product = finops.iloc[
        finops["request_failure_rate_pct"].argmax()
    ]

    insight_columns = st.columns(3)

    with insight_columns[0]:
        st.markdown("#### Cost Concentration")
        st.write(
            f"**{highest_cost_product['product_name']}** has the "
            f"largest estimated cloud cost at "
            f"**{money(highest_cost_product['estimated_cost_usd'])}**."
        )

    with insight_columns[1]:
        st.markdown("#### Unit Cost Signal")
        st.write(
            f"**{highest_unit_cost['product_name']}** has the "
            f"highest cost per compute hour at "
            f"**{money(highest_unit_cost['cost_per_compute_hour'])}**."
        )

    with insight_columns[2]:
        st.markdown("#### Reliability Signal")
        st.write(
            f"**{highest_failure_product['product_name']}** has the "
            f"highest product-level request failure rate at "
            f"**{pct(highest_failure_product['request_failure_rate_pct'])}**."
        )

    if not customers.empty:

        st.markdown("#### Customer Optimization Signal")

        weakest_customers = customers.sort_values(
            [
                "cloud_cost_pct_of_revenue",
                "cloud_cost_usd",
            ],
            ascending=[False, False],
        ).head(5)

        st.dataframe(
            weakest_customers[
                [
                    "customer_id",
                    "customer_name",
                    "customer_segment",
                    "lifetime_revenue_usd",
                    "cloud_cost_usd",
                    "cloud_cost_pct_of_revenue",
                    "cloud_efficiency_band",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    if not sustainability.empty:

        best_carbon = sustainability.sort_values(
            "carbon_efficiency_rank"
        ).iloc[0]

        best_renewable = sustainability.sort_values(
            "renewable_rank"
        ).iloc[0]

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                "#### Carbon Efficiency Leader"
            )
            st.write(
                f"**{best_carbon['datacenter_name']}** currently "
                f"ranks #1 for carbon efficiency with "
                f"**{decimal(best_carbon['carbon_per_compute_hour_kg'], 6)} "
                f"kg per compute hour**."
            )

        with c2:
            st.markdown(
                "#### Renewable Energy Leader"
            )
            st.write(
                f"**{best_renewable['datacenter_name']}** currently "
                f"ranks #1 for renewable energy at "
                f"**{pct(best_renewable['renewable_energy_pct'])}**."
            )

    st.caption(
        "These are descriptive analytical signals generated from the current "
        "semantic-layer data. They are not automated operational decisions."
    )