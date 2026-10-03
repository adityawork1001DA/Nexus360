from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.components.insight import (
    render_chart_guide,
    render_insight_panel,
    render_metric_dictionary,
)
from src.ui.components.kpi import render_kpi
from src.ui.data_service import load_executive_bundle
from src.ui.theme import render_page_header


def _first_numeric(
    dataframe: pd.DataFrame,
    candidates: list[str],
    default: float = 0.0,
) -> float:

    if dataframe.empty:
        return default

    for column in candidates:

        if column not in dataframe.columns:
            continue

        value = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).iloc[0]

        if pd.notna(value):
            return float(value)

    return default


def _sum_numeric(
    dataframe: pd.DataFrame,
    column: str,
) -> float:

    if dataframe.empty or column not in dataframe.columns:
        return 0.0

    return float(
        pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )


def _apply_plotly_layout(
    figure,
    height: int = 420,
):
    """
    Apply shared Nexus360 Plotly formatting.
    """

    figure.update_layout(
        height=height,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#CBD5E1",
        ),
        legend_title_text="",
    )

    return figure


def render() -> None:
    """
    Nexus360 Executive Command Center V2.
    """

    render_page_header(
        title="Executive Command Center",
        subtitle=(
            "Enterprise-level revenue, profitability, "
            "customer, product and commercial-risk intelligence."
        ),
        eyebrow="NEXUS 360 • EXECUTIVE INTELLIGENCE",
    )

    st.info(
        """
**What this page answers:**  
How large is the business, how profitable is it, where is
revenue coming from, and where is the most significant
commercial exposure?
        """
    )

    with st.spinner(
        "Loading executive intelligence..."
    ):
        data = load_executive_bundle()

    executive = data["executive"].copy()
    monthly = data["monthly"].copy()
    regional = data["regional"].copy()
    products = data["products"].copy()
    risk = data["risk"].copy()
    health = data["business_health"].copy()

    # ==========================================================
    # KPI CALCULATIONS
    # ==========================================================

    total_revenue = _first_numeric(
        executive,
        [
            "total_revenue_usd",
            "net_revenue_usd",
            "revenue_usd",
        ],
    )

    if total_revenue <= 0:
        total_revenue = _sum_numeric(
            monthly,
            "net_revenue_usd",
        )

    active_customers = _first_numeric(
        executive,
        [
            "active_customers",
            "total_customers",
            "customers",
        ],
    )

    gross_margin = _first_numeric(
        executive,
        [
            "gross_margin_pct",
            "margin_pct",
        ],
    )

    revenue_at_risk = _sum_numeric(
        risk,
        "revenue_at_risk_usd",
    )

    business_health = _first_numeric(
        health,
        [
            "business_health_score",
            "health_score",
            "score",
        ],
    )

    # ==========================================================
    # KPI SECTION
    # ==========================================================

    st.subheader("Enterprise Snapshot")

    st.caption(
        "High-level indicators summarizing commercial scale, "
        "profitability and modeled exposure."
    )

    columns = st.columns(
        5,
        gap="medium",
    )

    with columns[0]:
        render_kpi(
            "Total Revenue",
            total_revenue,
            kind="currency",
            detail="Net enterprise revenue",
            sentiment="positive",
        )

    with columns[1]:
        render_kpi(
            "Active Customers",
            active_customers,
            kind="number",
            detail="Current customer footprint",
            sentiment="neutral",
        )

    with columns[2]:
        render_kpi(
            "Gross Margin",
            gross_margin,
            kind="percent",
            detail="Revenue retained after direct cost",
            sentiment=(
                "positive"
                if gross_margin >= 50
                else "neutral"
            ),
        )

    with columns[3]:
        render_kpi(
            "Revenue at Risk",
            revenue_at_risk,
            kind="currency",
            detail="Modeled commercial exposure",
            sentiment="negative",
        )

    with columns[4]:
        render_kpi(
            "Business Health",
            business_health,
            kind="number",
            detail="Composite analytical score",
            sentiment=(
                "positive"
                if business_health >= 70
                else "neutral"
            ),
        )

    st.caption(
        "ⓘ Definitions and formulas for these KPIs are available "
        "in the Metric Dictionary at the bottom of this page."
    )

    st.divider()

    # ==========================================================
    # REVENUE + PRODUCT
    # ==========================================================

    left, right = st.columns(
        [1.6, 1],
        gap="large",
    )

    with left:

        st.subheader("Revenue Trajectory")

        st.caption(
            "Monthly net revenue shows the direction and "
            "consistency of enterprise commercial performance."
        )

        if {
            "revenue_month",
            "net_revenue_usd",
        }.issubset(monthly.columns):

            chart_data = monthly[
                [
                    "revenue_month",
                    "net_revenue_usd",
                ]
            ].copy()

            chart_data["revenue_month"] = pd.to_datetime(
                chart_data["revenue_month"],
                errors="coerce",
            )

            chart_data["net_revenue_usd"] = pd.to_numeric(
                chart_data["net_revenue_usd"],
                errors="coerce",
            )

            chart_data = (
                chart_data
                .dropna()
                .sort_values("revenue_month")
            )

            figure = px.line(
                chart_data,
                x="revenue_month",
                y="net_revenue_usd",
                markers=True,
                labels={
                    "revenue_month": "Month",
                    "net_revenue_usd": "Net Revenue (USD)",
                },
            )

            figure.update_traces(
                line=dict(width=3)
            )

            _apply_plotly_layout(
                figure,
                420,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

            render_chart_guide(
                title="Revenue Trajectory",
                definition=(
                    "Tracks net revenue generated during each "
                    "month across the enterprise."
                ),
                business_question=(
                    "Is revenue expanding, contracting, seasonal "
                    "or unusually volatile?"
                ),
                interpretation=[
                    (
                        "A sustained upward slope suggests "
                        "commercial expansion."
                    ),
                    (
                        "A sustained downward slope may indicate "
                        "revenue contraction."
                    ),
                    (
                        "Sharp spikes or drops should be "
                        "investigated for product, customer, "
                        "regional or timing effects."
                    ),
                ],
                business_use=[
                    "Revenue planning and forecasting.",
                    "Trend and seasonality analysis.",
                    "Executive performance monitoring.",
                    "Anomaly investigation.",
                ],
            )

        else:
            st.warning(
                "Required monthly revenue columns are unavailable."
            )

    with right:

        st.subheader("Top Products by Revenue")

        st.caption(
            "Ranks products according to their contribution "
            "to enterprise revenue."
        )

        if {
            "product_name",
            "revenue_usd",
        }.issubset(products.columns):

            product_data = products[
                [
                    "product_name",
                    "revenue_usd",
                ]
            ].copy()

            product_data["revenue_usd"] = pd.to_numeric(
                product_data["revenue_usd"],
                errors="coerce",
            )

            product_data = (
                product_data
                .dropna()
                .nlargest(
                    8,
                    "revenue_usd",
                )
                .sort_values(
                    "revenue_usd"
                )
            )

            figure = px.bar(
                product_data,
                x="revenue_usd",
                y="product_name",
                orientation="h",
                labels={
                    "revenue_usd": "Revenue (USD)",
                    "product_name": "Product",
                },
            )

            _apply_plotly_layout(
                figure,
                420,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

            render_chart_guide(
                title="Top Products by Revenue",
                definition=(
                    "Compares total net revenue generated by "
                    "individual products."
                ),
                business_question=(
                    "Which products contribute most strongly "
                    "to enterprise revenue?"
                ),
                interpretation=[
                    (
                        "Longer bars represent larger revenue "
                        "contribution."
                    ),
                    (
                        "A highly concentrated ranking may "
                        "indicate dependence on a small number "
                        "of products."
                    ),
                ],
                business_use=[
                    "Portfolio prioritization.",
                    "Cross-sell strategy.",
                    "Investment allocation.",
                    "Revenue concentration analysis.",
                ],
            )

        else:
            st.warning(
                "Product revenue information is unavailable."
            )

    # ==========================================================
    # REGIONAL PERFORMANCE
    # ==========================================================

    st.divider()

    st.subheader("Regional Performance")

    st.caption(
        "Compares commercial contribution across geographic "
        "operating regions."
    )

    region_column = next(
        (
            column
            for column in [
                "region_name",
                "region_code",
                "geography_group",
            ]
            if column in regional.columns
        ),
        None,
    )

    revenue_column = next(
        (
            column
            for column in [
                "revenue_usd",
                "net_revenue_usd",
                "total_revenue_usd",
            ]
            if column in regional.columns
        ),
        None,
    )

    if (
        region_column is not None
        and revenue_column is not None
    ):

        region_data = regional[
            [
                region_column,
                revenue_column,
            ]
        ].copy()

        region_data[revenue_column] = pd.to_numeric(
            region_data[revenue_column],
            errors="coerce",
        )

        region_data = (
            region_data
            .dropna()
            .sort_values(
                revenue_column,
                ascending=False,
            )
        )

        figure = px.bar(
            region_data,
            x=region_column,
            y=revenue_column,
            labels={
                region_column: "Region",
                revenue_column: "Revenue (USD)",
            },
        )

        _apply_plotly_layout(
            figure,
            390,
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

        render_chart_guide(
            title="Regional Performance",
            definition=(
                "Compares revenue contribution across geographic "
                "regions."
            ),
            business_question=(
                "Which regions are driving enterprise growth "
                "and where is commercial contribution weaker?"
            ),
            interpretation=[
                (
                    "Higher bars represent greater revenue "
                    "contribution."
                ),
                (
                    "Large differences between regions may "
                    "indicate market concentration."
                ),
                (
                    "Regional revenue should eventually be "
                    "interpreted alongside customer count, "
                    "market size and growth."
                ),
            ],
            business_use=[
                "Geographic investment decisions.",
                "Market expansion strategy.",
                "Sales resource allocation.",
            ],
        )

    # ==========================================================
    # COMMERCIAL RISK
    # ==========================================================

    st.divider()

    st.subheader("Commercial Risk Intelligence")

    st.caption(
        "Revenue at Risk estimates commercial exposure associated "
        "with customers showing elevated analytical risk."
    )

    if not risk.empty:

        risk_data = risk.copy()

        if "revenue_at_risk_usd" in risk_data.columns:

            risk_data["revenue_at_risk_usd"] = pd.to_numeric(
                risk_data["revenue_at_risk_usd"],
                errors="coerce",
            )

            risk_data = risk_data.sort_values(
                "revenue_at_risk_usd",
                ascending=False,
            )

        chart_col, table_col = st.columns(
            [1, 1.8],
            gap="large",
        )

        with chart_col:

            if "revenue_risk_band" in risk_data.columns:

                distribution = (
                    risk_data[
                        "revenue_risk_band"
                    ]
                    .fillna("Unknown")
                    .value_counts()
                    .rename_axis("Risk Band")
                    .reset_index(name="Customers")
                )

                figure = px.pie(
                    distribution,
                    names="Risk Band",
                    values="Customers",
                    hole=0.6,
                )

                _apply_plotly_layout(
                    figure,
                    400,
                )

                st.plotly_chart(
                    figure,
                    width="stretch",
                )

        with table_col:

            st.markdown(
                "**Highest Commercial Exposure Accounts**"
            )

            preferred = [
                "revenue_at_risk_rank",
                "customer_id",
                "customer_name",
                "customer_segment",
                "industry",
                "lifetime_revenue_usd",
                "composite_risk_score",
                "revenue_at_risk_usd",
                "revenue_risk_band",
            ]

            available = [
                column
                for column in preferred
                if column in risk_data.columns
            ]

            st.dataframe(
                risk_data[
                    available
                ].head(20),
                width="stretch",
                hide_index=True,
            )

        render_chart_guide(
            title="Commercial Risk Intelligence",
            definition=(
                "Combines customer commercial value with "
                "analytical risk signals to estimate revenue "
                "exposure."
            ),
            business_question=(
                "Which customer relationships deserve priority "
                "for retention and risk investigation?"
            ),
            interpretation=[
                (
                    "Revenue at Risk is an exposure estimate, "
                    "not guaranteed future revenue loss."
                ),
                (
                    "High-value and high-risk customers deserve "
                    "greater investigation."
                ),
                (
                    "Risk bands make prioritization easier, "
                    "while the underlying score provides more "
                    "granular ranking."
                ),
            ],
            business_use=[
                "Retention prioritization.",
                "Account-management triage.",
                "Commercial risk monitoring.",
            ],
            caveat=(
                "This is a portfolio analytical model based on "
                "Nexus360 project data. It should not be "
                "interpreted as an audited financial forecast."
            ),
        )

        if "revenue_at_risk_usd" in risk_data.columns:

            total_risk = (
                risk_data[
                    "revenue_at_risk_usd"
                ]
                .fillna(0)
                .sum()
            )

            top_ten = (
                risk_data[
                    "revenue_at_risk_usd"
                ]
                .fillna(0)
                .nlargest(10)
                .sum()
            )

            concentration = (
                top_ten
                / total_risk
                * 100
                if total_risk > 0
                else 0
            )

            render_insight_panel(
                metric=(
                    f"Revenue at Risk = "
                    f"${total_risk:,.0f}"
                ),
                insight=(
                    f"The ten largest exposure accounts represent "
                    f"{concentration:,.2f}% of modeled revenue "
                    f"at risk."
                ),
                potential_action=(
                    "Review the highest-value, highest-risk "
                    "accounts first and identify whether support, "
                    "renewal or usage signals are driving risk."
                ),
                warning=True,
            )

    # ==========================================================
    # METRIC DICTIONARY
    # ==========================================================

    st.divider()

    render_metric_dictionary(
        [
            {
                "metric": "Total Revenue",
                "definition": (
                    "Total net revenue recorded across the "
                    "enterprise analytical period."
                ),
                "formula": (
                    "Total Revenue = SUM(Net Revenue USD)"
                ),
                "interpretation": (
                    "Measures the commercial scale represented "
                    "in Nexus360."
                ),
            },
            {
                "metric": "Active Customers",
                "definition": (
                    "Number of customers classified as active "
                    "in the customer dimension."
                ),
                "formula": (
                    "Active Customers = COUNT(Customers "
                    "where Status = Active)"
                ),
                "interpretation": (
                    "Represents the current active customer base."
                ),
            },
            {
                "metric": "Gross Margin %",
                "definition": (
                    "Percentage of net revenue remaining after "
                    "estimated direct cost."
                ),
                "formula": (
                    "Gross Margin % = "
                    "Gross Profit / Net Revenue × 100"
                ),
                "interpretation": (
                    "Higher values indicate a larger proportion "
                    "of revenue remains after modeled direct cost."
                ),
            },
            {
                "metric": "Revenue at Risk",
                "definition": (
                    "Modeled commercial exposure associated with "
                    "customers displaying elevated risk signals."
                ),
                "formula": (
                    "Customer Revenue × Nexus360 Risk Exposure "
                    "Methodology"
                ),
                "interpretation": (
                    "It is a prioritization metric and does not "
                    "mean that this revenue will definitely be lost."
                ),
            },
            {
                "metric": "Business Health Score",
                "definition": (
                    "Composite Nexus360 indicator combining "
                    "multiple business-performance dimensions."
                ),
                "formula": (
                    "Weighted composite of Nexus360 "
                    "business-health indicators"
                ),
                "interpretation": (
                    "Provides a simplified enterprise health "
                    "signal; underlying component metrics should "
                    "be reviewed before making decisions."
                ),
            },
        ]
    )