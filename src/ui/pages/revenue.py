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
from src.ui.data_service import load_analytics_view
from src.ui.theme import render_page_header


def _layout(
    figure,
    height: int = 420,
):
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

    render_page_header(
        title="Revenue Intelligence",
        subtitle=(
            "Trend, growth, profitability, product concentration "
            "and geographic revenue analysis."
        ),
        eyebrow="NEXUS 360 • COMMERCIAL ANALYTICS",
    )

    st.info(
        """
**What this page answers:**  
How is revenue changing over time, how profitable is that
revenue, which products and regions drive it, and are there
signals of unusual revenue behavior?
        """
    )

    monthly = load_analytics_view(
        "v_monthly_revenue"
    ).copy()

    products = load_analytics_view(
        "v_product_revenue_rank"
    ).copy()

    regional = load_analytics_view(
        "v_regional_performance"
    ).copy()

    anomalies = load_analytics_view(
        "v_revenue_anomalies"
    ).copy()

    # ==========================================================
    # PREP MONTHLY
    # ==========================================================

    if "revenue_month" in monthly.columns:
        monthly["revenue_month"] = pd.to_datetime(
            monthly["revenue_month"],
            errors="coerce",
        )

    for column in [
        "net_revenue_usd",
        "estimated_cost_usd",
        "gross_profit_usd",
        "gross_margin_pct",
        "mom_growth_pct",
    ]:
        if column in monthly.columns:
            monthly[column] = pd.to_numeric(
                monthly[column],
                errors="coerce",
            )

    monthly = monthly.sort_values(
        "revenue_month"
    )

    # ==========================================================
    # KPI
    # ==========================================================

    total_revenue = (
        monthly["net_revenue_usd"]
        .fillna(0)
        .sum()
        if "net_revenue_usd" in monthly.columns
        else 0
    )

    total_profit = (
        monthly["gross_profit_usd"]
        .fillna(0)
        .sum()
        if "gross_profit_usd" in monthly.columns
        else 0
    )

    total_cost = (
        monthly["estimated_cost_usd"]
        .fillna(0)
        .sum()
        if "estimated_cost_usd" in monthly.columns
        else 0
    )

    weighted_margin = (
        total_profit / total_revenue * 100
        if total_revenue > 0
        else 0
    )

    latest_growth = 0.0

    if (
        "mom_growth_pct" in monthly.columns
        and not monthly.empty
    ):
        growth_values = (
            monthly["mom_growth_pct"]
            .dropna()
        )

        if not growth_values.empty:
            latest_growth = float(
                growth_values.iloc[-1]
            )

    kpis = st.columns(
        4,
        gap="medium",
    )

    with kpis[0]:
        render_kpi(
            "Net Revenue",
            total_revenue,
            kind="currency",
            detail="Revenue after discounts",
            sentiment="positive",
        )

    with kpis[1]:
        render_kpi(
            "Gross Profit",
            total_profit,
            kind="currency",
            detail="Revenue minus estimated direct cost",
            sentiment="positive",
        )

    with kpis[2]:
        render_kpi(
            "Gross Margin",
            weighted_margin,
            kind="percent",
            detail="Profitability ratio",
            sentiment="positive",
        )

    with kpis[3]:
        render_kpi(
            "Latest MoM Growth",
            latest_growth,
            kind="percent",
            detail="Change versus previous month",
            sentiment=(
                "positive"
                if latest_growth >= 0
                else "negative"
            ),
        )

    st.divider()

    # ==========================================================
    # REVENUE TREND
    # ==========================================================

    st.subheader(
        "Revenue and Gross Profit Trend"
    )

    st.caption(
        "Compares monthly commercial scale with the gross profit "
        "retained after modeled direct costs."
    )

    required = {
        "revenue_month",
        "net_revenue_usd",
        "gross_profit_usd",
    }

    if required.issubset(
        monthly.columns
    ):

        trend = monthly[
            [
                "revenue_month",
                "net_revenue_usd",
                "gross_profit_usd",
            ]
        ].dropna()

        long_data = trend.melt(
            id_vars="revenue_month",
            value_vars=[
                "net_revenue_usd",
                "gross_profit_usd",
            ],
            var_name="Metric",
            value_name="USD",
        )

        long_data["Metric"] = (
            long_data["Metric"]
            .replace(
                {
                    "net_revenue_usd":
                        "Net Revenue",

                    "gross_profit_usd":
                        "Gross Profit",
                }
            )
        )

        figure = px.line(
            long_data,
            x="revenue_month",
            y="USD",
            color="Metric",
            markers=True,
            labels={
                "revenue_month": "Month",
                "USD": "USD",
            },
        )

        _layout(
            figure,
            430,
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

        render_chart_guide(
            title="Revenue and Gross Profit Trend",
            definition=(
                "Shows monthly net revenue alongside gross "
                "profit."
            ),
            business_question=(
                "Is revenue growth translating into additional "
                "gross profit?"
            ),
            interpretation=[
                (
                    "Both lines rising suggests commercial "
                    "growth with increasing gross profit."
                ),
                (
                    "Revenue rising faster than gross profit "
                    "may indicate margin pressure."
                ),
                (
                    "A widening distance between revenue and "
                    "gross profit represents increasing modeled "
                    "direct cost."
                ),
            ],
            business_use=[
                "Profitability monitoring.",
                "Pricing analysis.",
                "Cost-efficiency investigation.",
            ],
        )

    # ==========================================================
    # PRODUCT + REGION
    # ==========================================================

    left, right = st.columns(
        2,
        gap="large",
    )

    with left:

        st.subheader(
            "Product Revenue Concentration"
        )

        if {
            "product_name",
            "revenue_usd",
        }.issubset(products.columns):

            product_chart = products.copy()

            product_chart["revenue_usd"] = pd.to_numeric(
                product_chart["revenue_usd"],
                errors="coerce",
            )

            product_chart = (
                product_chart
                .dropna(
                    subset=[
                        "product_name",
                        "revenue_usd",
                    ]
                )
                .nlargest(
                    10,
                    "revenue_usd",
                )
                .sort_values(
                    "revenue_usd"
                )
            )

            figure = px.bar(
                product_chart,
                x="revenue_usd",
                y="product_name",
                orientation="h",
                labels={
                    "revenue_usd": "Revenue (USD)",
                    "product_name": "Product",
                },
            )

            _layout(
                figure,
                420,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

            render_chart_guide(
                title="Product Revenue Concentration",
                definition=(
                    "Ranks products according to total "
                    "revenue contribution."
                ),
                business_question=(
                    "Is enterprise revenue diversified or "
                    "concentrated in a small product portfolio?"
                ),
                interpretation=[
                    (
                        "A dominant product may represent both "
                        "commercial strength and concentration risk."
                    ),
                    (
                        "Smaller products may represent expansion "
                        "or cross-sell opportunities."
                    ),
                ],
                business_use=[
                    "Portfolio strategy.",
                    "Cross-sell planning.",
                    "Concentration-risk assessment.",
                ],
            )

    with right:

        st.subheader(
            "Regional Revenue Mix"
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

            region_chart = regional[
                [
                    region_column,
                    revenue_column,
                ]
            ].copy()

            region_chart[revenue_column] = pd.to_numeric(
                region_chart[revenue_column],
                errors="coerce",
            )

            region_chart = region_chart.dropna()

            figure = px.pie(
                region_chart,
                names=region_column,
                values=revenue_column,
                hole=0.55,
            )

            _layout(
                figure,
                420,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

            render_chart_guide(
                title="Regional Revenue Mix",
                definition=(
                    "Shows each region's share of enterprise "
                    "revenue."
                ),
                business_question=(
                    "How geographically diversified is revenue?"
                ),
                interpretation=[
                    (
                        "Large slices indicate stronger revenue "
                        "concentration in that geography."
                    ),
                    (
                        "A balanced distribution indicates greater "
                        "geographic diversification."
                    ),
                ],
                business_use=[
                    "Geographic diversification analysis.",
                    "Market prioritization.",
                    "Regional planning.",
                ],
            )

    # ==========================================================
    # ANOMALIES
    # ==========================================================

    st.divider()

    st.subheader(
        "Revenue Anomaly Detection"
    )

    st.caption(
        "Statistical monitoring highlights dates where revenue "
        "behavior differs materially from its normal pattern."
    )

    if not anomalies.empty:

        anomaly_data = anomalies.copy()

        if "full_date" in anomaly_data.columns:
            anomaly_data["full_date"] = pd.to_datetime(
                anomaly_data["full_date"],
                errors="coerce",
            )

        if "daily_revenue" in anomaly_data.columns:
            anomaly_data["daily_revenue"] = pd.to_numeric(
                anomaly_data["daily_revenue"],
                errors="coerce",
            )

        if {
            "full_date",
            "daily_revenue",
        }.issubset(anomaly_data.columns):

            figure = px.scatter(
                anomaly_data,
                x="full_date",
                y="daily_revenue",
                color=(
                    "anomaly_status"
                    if "anomaly_status"
                    in anomaly_data.columns
                    else None
                ),
                labels={
                    "full_date": "Date",
                    "daily_revenue": "Daily Revenue (USD)",
                },
            )

            _layout(
                figure,
                420,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

        render_chart_guide(
            title="Revenue Anomaly Detection",
            definition=(
                "Uses statistical deviation from expected "
                "revenue behavior to flag unusual observations."
            ),
            business_question=(
                "Which revenue observations deserve additional "
                "investigation?"
            ),
            interpretation=[
                (
                    "An anomaly means unusual statistical "
                    "behavior, not necessarily an error."
                ),
                (
                    "Positive anomalies may represent unusually "
                    "strong transactions or events."
                ),
                (
                    "Negative anomalies may indicate weak "
                    "commercial activity or data-quality issues."
                ),
            ],
            business_use=[
                "Financial monitoring.",
                "Data-quality investigation.",
                "Commercial event analysis.",
            ],
            caveat=(
                "Statistical anomaly detection identifies unusual "
                "patterns. It does not determine their underlying "
                "business cause."
            ),
        )

    # ==========================================================
    # AUTOMATED INSIGHT
    # ==========================================================

    if not monthly.empty:

        render_insight_panel(
            metric=(
                f"Gross Margin = "
                f"{weighted_margin:,.2f}%"
            ),
            insight=(
                "This represents the proportion of net revenue "
                "remaining as gross profit after modeled direct "
                "cost."
            ),
            potential_action=(
                "Track this metric alongside revenue growth. "
                "Revenue expansion with declining margin can "
                "signal pricing or cost pressure."
            ),
        )

    # ==========================================================
    # DATA TABLE
    # ==========================================================

    st.divider()

    with st.expander(
        "View monthly analytical dataset",
        expanded=False,
    ):
        st.dataframe(
            monthly,
            width="stretch",
            hide_index=True,
        )

    # ==========================================================
    # DICTIONARY
    # ==========================================================

    render_metric_dictionary(
        [
            {
                "metric": "Net Revenue",
                "definition": (
                    "Revenue remaining after discounts and "
                    "commercial adjustments represented in the "
                    "warehouse."
                ),
                "formula": (
                    "Net Revenue = Gross Revenue - Discounts"
                ),
                "interpretation": (
                    "Primary commercial revenue measure used "
                    "throughout Nexus360."
                ),
            },
            {
                "metric": "Gross Profit",
                "definition": (
                    "Net revenue remaining after estimated "
                    "direct costs."
                ),
                "formula": (
                    "Gross Profit = Net Revenue - "
                    "Estimated Direct Cost"
                ),
                "interpretation": (
                    "Measures absolute gross profitability."
                ),
            },
            {
                "metric": "Gross Margin %",
                "definition": (
                    "Gross profit expressed as a percentage "
                    "of net revenue."
                ),
                "formula": (
                    "Gross Margin % = "
                    "Gross Profit / Net Revenue × 100"
                ),
                "interpretation": (
                    "Measures relative profitability independent "
                    "of revenue scale."
                ),
            },
            {
                "metric": "Month-over-Month Growth %",
                "definition": (
                    "Percentage change in revenue compared with "
                    "the immediately preceding month."
                ),
                "formula": (
                    "MoM Growth % = "
                    "(Current Month Revenue - Previous Month Revenue) "
                    "/ Previous Month Revenue × 100"
                ),
                "interpretation": (
                    "Positive values represent monthly expansion; "
                    "negative values represent contraction."
                ),
            },
            {
                "metric": "Revenue Anomaly Z-Score",
                "definition": (
                    "Standardized measure of how far an observation "
                    "lies from its expected revenue level."
                ),
                "formula": (
                    "Z = (Observed Revenue - Mean Revenue) "
                    "/ Revenue Standard Deviation"
                ),
                "interpretation": (
                    "Larger absolute values indicate more unusual "
                    "revenue behavior."
                ),
            },
        ]
    )