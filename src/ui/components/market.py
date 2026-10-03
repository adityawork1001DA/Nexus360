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

    if abs(value) >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:,.2f}T"

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.2f}K"

    return f"${value:,.2f}"


def number(value: float | int | None) -> str:
    value = float(value or 0)

    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:,.2f}T"

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:,.2f}K"

    return f"{value:,.0f}"


def pct(value: float | int | None) -> str:
    return f"{float(value or 0):,.2f}%"


def decimal(
    value: float | int | None,
    digits: int = 2,
) -> str:
    return f"{float(value or 0):,.{digits}f}"


def safe_divide(
    numerator: float,
    denominator: float,
    multiplier: float = 1.0,
) -> float:

    if denominator is None:
        return 0.0

    denominator = float(denominator)

    if denominator == 0:
        return 0.0

    return (
        float(numerator)
        / denominator
        * multiplier
    )


# ============================================================
# EXPLANATION COMPONENT
# ============================================================

def section_explainer(
    title: str,
    definition: str,
    interpretation: str,
    business_use: str,
    caution: str | None = None,
) -> None:

    with st.expander(
        f"Understanding {title}"
    ):

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


# ============================================================
# EXECUTIVE KPIs
# ============================================================

def render_market_kpis(
    fx: pd.DataFrame,
    macro: pd.DataFrame,
    opportunity: pd.DataFrame,
) -> None:

    total_revenue = (
        macro["net_revenue_usd"].sum()
    )

    total_customers = (
        macro["total_customers"].sum()
    )

    total_gdp = (
        macro["gdp_usd"].sum()
    )

    weighted_internet = safe_divide(
        (
            macro["internet_users_pct"]
            * macro["population"]
        ).sum(),
        macro["population"].sum(),
    )

    weighted_ai_adoption = safe_divide(
        macro["ai_customers"].sum(),
        macro["total_customers"].sum(),
        100,
    )

    average_fx_risk = (
        fx["fx_risk_score"].mean()
        if not fx.empty
        else 0
    )

    highest_opportunity = (
        opportunity.sort_values(
            "opportunity_rank"
        ).iloc[0]
        if not opportunity.empty
        else None
    )

    row1 = st.columns(4)

    row1[0].metric(
        "Global Revenue",
        money(total_revenue),
    )

    row1[1].metric(
        "Customer Base",
        number(total_customers),
    )

    row1[2].metric(
        "Addressed Market GDP",
        money(total_gdp),
    )

    row1[3].metric(
        "Population-Weighted Internet Usage",
        pct(weighted_internet),
    )

    row2 = st.columns(4)

    row2[0].metric(
        "AI Customer Adoption",
        pct(weighted_ai_adoption),
    )

    row2[1].metric(
        "Average FX Risk Score",
        decimal(
            average_fx_risk,
            2,
        ),
    )

    row2[2].metric(
        "Currencies Monitored",
        f"{fx['currency_code'].nunique():,}",
    )

    if highest_opportunity is not None:
        row2[3].metric(
            "Top Market Opportunity",
            str(
                highest_opportunity[
                    "country_name"
                ]
            ),
            f"Score {highest_opportunity['market_opportunity_score']:.1f}",
        )
    else:
        row2[3].metric(
            "Top Market Opportunity",
            "N/A",
        )

    section_explainer(
        "Global Market KPIs",
        (
            "These KPIs summarize the current commercial footprint, "
            "economic environment, digital readiness, AI adoption and "
            "currency exposure represented in Nexus 360."
        ),
        (
            "Revenue and customer base describe current business scale. "
            "GDP and internet usage provide external market context. "
            "AI adoption indicates penetration within the existing customer "
            "base, while FX risk summarizes currency-related exposure."
        ),
        (
            "Together these measures provide executives with a combined "
            "internal and external view of international performance."
        ),
    )


# ============================================================
# FX INTELLIGENCE
# ============================================================

def render_fx_exposure_chart(
    fx: pd.DataFrame,
) -> None:

    st.subheader(
        "Revenue Exposure by Currency"
    )

    data = fx.sort_values(
        "revenue_exposure_pct",
        ascending=True,
    ).copy()

    fig = px.bar(
        data,
        x="revenue_exposure_pct",
        y="currency_code",
        orientation="h",
        text="revenue_exposure_pct",
        hover_data={
            "currency_name": True,
            "net_revenue_usd": ":,.2f",
            "net_revenue_local": ":,.2f",
            "transaction_count": ":,",
            "customer_count": ":,",
            "fx_risk_score": ":.2f",
            "fx_risk_band": True,
        },
        labels={
            "revenue_exposure_pct":
                "Revenue Exposure (%)",
            "currency_code":
                "Currency",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(
        height=max(
            450,
            len(data) * 48,
        ),
        yaxis_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Revenue Exposure by Currency",
        (
            "Revenue Exposure % measures the proportion of total "
            "business revenue associated with each transaction currency."
        ),
        (
            "A currency with a larger revenue share represents a larger "
            "commercial exposure. Exposure alone does not imply risk; it "
            "must be interpreted alongside volatility."
        ),
        (
            "Treasury and finance teams use currency exposure to understand "
            "where exchange-rate movements could have the greatest business "
            "impact."
        ),
    )


def render_fx_risk_matrix(
    fx: pd.DataFrame,
) -> None:

    st.subheader(
        "FX Exposure vs Volatility"
    )

    data = fx.copy()

    fig = px.scatter(
        data,
        x="fx_coefficient_variation_pct",
        y="revenue_exposure_pct",
        size="net_revenue_usd",
        hover_name="currency_code",
        hover_data={
            "currency_name": True,
            "average_market_fx_rate": ":.6f",
            "minimum_fx_rate": ":.6f",
            "maximum_fx_rate": ":.6f",
            "fx_volatility": ":.6f",
            "fx_risk_score": ":.2f",
            "fx_risk_band": True,
            "fx_risk_rank": True,
        },
        labels={
            "fx_coefficient_variation_pct":
                "FX Coefficient of Variation (%)",
            "revenue_exposure_pct":
                "Revenue Exposure (%)",
        },
    )

    if not data.empty:

        fig.add_vline(
            x=data[
                "fx_coefficient_variation_pct"
            ].median(),
            line_dash="dash",
        )

        fig.add_hline(
            y=data[
                "revenue_exposure_pct"
            ].median(),
            line_dash="dash",
        )

    fig.update_layout(
        height=540
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "FX Exposure vs Volatility",
        (
            "This matrix combines commercial currency exposure with "
            "historical exchange-rate variability."
        ),
        (
            "Currencies toward the upper-right combine relatively high "
            "revenue exposure with relatively high FX variability and "
            "therefore deserve greater treasury attention."
        ),
        (
            "The matrix helps distinguish currencies that are merely "
            "volatile from currencies whose volatility could materially "
            "affect business performance."
        ),
        caution=(
            "Historical volatility does not predict future exchange rates. "
            "This dashboard provides analytical risk signals rather than "
            "trading or hedging recommendations."
        ),
    )


def render_fx_rate_range(
    fx: pd.DataFrame,
) -> None:

    st.subheader(
        "Observed FX Rate Range"
    )

    data = fx.sort_values(
        "fx_risk_rank"
    ).copy()

    fig = go.Figure()

    for _, row in data.iterrows():

        fig.add_trace(
            go.Scatter(
                x=[
                    row["minimum_fx_rate"],
                    row["maximum_fx_rate"],
                ],
                y=[
                    row["currency_code"],
                    row["currency_code"],
                ],
                mode="lines+markers",
                name=row["currency_code"],
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['currency_code']}</b><br>"
                    f"Minimum: {row['minimum_fx_rate']:.6f}<br>"
                    f"Maximum: {row['maximum_fx_rate']:.6f}"
                    "<extra></extra>"
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[
                    row[
                        "average_market_fx_rate"
                    ]
                ],
                y=[
                    row["currency_code"]
                ],
                mode="markers",
                marker={
                    "size": 11,
                    "symbol": "diamond",
                },
                name=(
                    f"{row['currency_code']} average"
                ),
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['currency_code']}</b><br>"
                    f"Average: "
                    f"{row['average_market_fx_rate']:.6f}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        height=max(
            450,
            len(data) * 55,
        ),
        xaxis_title="FX Rate to USD",
        yaxis_title="Currency",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Observed FX Rate Range",
        (
            "The horizontal range shows the minimum and maximum observed "
            "market FX rates in the available history. The diamond marks "
            "the average market rate."
        ),
        (
            "A wider range can indicate greater historical exchange-rate "
            "variation, although currencies operate at very different "
            "absolute rate levels."
        ),
        (
            "This gives treasury users a quick visual summary of the "
            "historical range underlying the FX volatility metrics."
        ),
    )


def render_fx_table(
    fx: pd.DataFrame,
) -> None:

    st.subheader(
        "Currency Risk Detail"
    )

    columns = [
        "revenue_exposure_rank",
        "fx_risk_rank",
        "currency_code",
        "currency_name",
        "transaction_count",
        "customer_count",
        "net_revenue_local",
        "net_revenue_usd",
        "revenue_exposure_pct",
        "average_transaction_fx_rate",
        "average_market_fx_rate",
        "minimum_fx_rate",
        "maximum_fx_rate",
        "fx_volatility",
        "fx_coefficient_variation_pct",
        "fx_risk_score",
        "fx_risk_band",
    ]

    data = fx[
        [
            column
            for column in columns
            if column in fx.columns
        ]
    ].sort_values(
        "fx_risk_rank"
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "net_revenue_usd":
                st.column_config.NumberColumn(
                    "Revenue USD",
                    format="$%.2f",
                ),
            "revenue_exposure_pct":
                st.column_config.ProgressColumn(
                    "Revenue Exposure",
                    min_value=0,
                    max_value=100,
                    format="%.2f%%",
                ),
            "fx_coefficient_variation_pct":
                st.column_config.NumberColumn(
                    "FX Variation",
                    format="%.4f%%",
                ),
            "fx_risk_score":
                st.column_config.NumberColumn(
                    "FX Risk Score",
                    format="%.2f",
                ),
        },
    )


# ============================================================
# MACROECONOMIC INTELLIGENCE
# ============================================================

def render_country_revenue(
    macro: pd.DataFrame,
) -> None:

    st.subheader(
        "Revenue by Country"
    )

    data = macro.sort_values(
        "net_revenue_usd",
        ascending=True,
    ).copy()

    fig = px.bar(
        data,
        x="net_revenue_usd",
        y="country_name",
        orientation="h",
        hover_data={
            "country_code": True,
            "total_customers": ":,",
            "transaction_count": ":,",
            "gross_profit_usd": ":,.2f",
            "gdp_usd": ":,.2f",
            "gdp_per_capita_usd": ":,.2f",
            "internet_users_pct": ":.2f",
            "inflation_pct": ":.2f",
            "ai_customer_adoption_pct": ":.2f",
        },
        labels={
            "net_revenue_usd":
                "Revenue (USD)",
            "country_name":
                "Country",
        },
    )

    fig.update_layout(
        height=max(
            470,
            len(data) * 48,
        ),
        yaxis_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Country Revenue",
        (
            "Country Revenue measures current Nexus 360 revenue attributed "
            "to customers in each market."
        ),
        (
            "Large revenue markets represent current commercial strength. "
            "However, current revenue should not be confused with future "
            "market opportunity."
        ),
        (
            "Comparing existing revenue with external market indicators "
            "helps identify both mature markets and potential whitespace."
        ),
    )


def render_gdp_revenue_matrix(
    macro: pd.DataFrame,
) -> None:

    st.subheader(
        "Economic Scale vs Nexus Revenue"
    )

    data = macro.copy()

    fig = px.scatter(
        data,
        x="gdp_usd",
        y="net_revenue_usd",
        size="population",
        hover_name="country_name",
        hover_data={
            "country_code": True,
            "total_customers": ":,",
            "gdp_per_capita_usd": ":,.2f",
            "internet_users_pct": ":.2f",
            "inflation_pct": ":.2f",
            "revenue_per_million_gdp": ":.4f",
            "ai_customer_adoption_pct": ":.2f",
        },
        labels={
            "gdp_usd":
                "GDP (USD)",
            "net_revenue_usd":
                "Nexus Revenue (USD)",
        },
    )

    fig.update_layout(
        height=550
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Economic Scale vs Nexus Revenue",
        (
            "The chart compares each country's economic size with current "
            "Nexus 360 revenue."
        ),
        (
            "A large economy with comparatively low Nexus revenue may "
            "represent commercial whitespace, while strong revenue in a "
            "smaller economy may indicate high penetration."
        ),
        (
            "Strategy teams can use this relationship as one input when "
            "evaluating geographic expansion and market prioritization."
        ),
        caution=(
            "GDP alone is not a measure of addressable cloud market size. "
            "The relationship should be combined with digital readiness, "
            "customer penetration and other market indicators."
        ),
    )


def render_digital_readiness(
    macro: pd.DataFrame,
) -> None:

    st.subheader(
        "Digital Readiness and AI Adoption"
    )

    data = macro.copy()

    fig = px.scatter(
        data,
        x="internet_users_pct",
        y="ai_customer_adoption_pct",
        size="net_revenue_usd",
        hover_name="country_name",
        hover_data={
            "gdp_per_capita_usd": ":,.2f",
            "inflation_pct": ":.2f",
            "total_customers": ":,",
            "ai_customers": ":,",
        },
        labels={
            "internet_users_pct":
                "Internet Users (%)",
            "ai_customer_adoption_pct":
                "AI Customer Adoption (%)",
        },
    )

    if not data.empty:

        fig.add_vline(
            x=data[
                "internet_users_pct"
            ].median(),
            line_dash="dash",
        )

        fig.add_hline(
            y=data[
                "ai_customer_adoption_pct"
            ].median(),
            line_dash="dash",
        )

    fig.update_layout(
        height=540
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Digital Readiness and AI Adoption",
        (
            "Internet Users % represents broad digital connectivity, while "
            "AI Customer Adoption % measures the share of current Nexus "
            "customers classified as AI customers."
        ),
        (
            "Markets with strong digital connectivity but relatively low "
            "AI adoption may represent AI expansion whitespace within the "
            "existing customer base."
        ),
        (
            "This view supports AI go-to-market planning and country-level "
            "product strategy."
        ),
    )


def render_macro_table(
    macro: pd.DataFrame,
) -> None:

    st.subheader(
        "Macroeconomic Country Detail"
    )

    columns = [
        "country_code",
        "country_name",
        "total_customers",
        "ai_customers",
        "transaction_count",
        "revenue_customers",
        "net_revenue_usd",
        "gross_profit_usd",
        "latest_economic_year",
        "gdp_usd",
        "population",
        "gdp_per_capita_usd",
        "internet_users_pct",
        "inflation_pct",
        "revenue_per_million_gdp",
        "revenue_per_capita_usd",
        "ai_customer_adoption_pct",
    ]

    data = macro[
        [
            column
            for column in columns
            if column in macro.columns
        ]
    ].sort_values(
        "net_revenue_usd",
        ascending=False,
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "net_revenue_usd":
                st.column_config.NumberColumn(
                    "Revenue",
                    format="$%.2f",
                ),
            "gross_profit_usd":
                st.column_config.NumberColumn(
                    "Gross Profit",
                    format="$%.2f",
                ),
            "gdp_usd":
                st.column_config.NumberColumn(
                    "GDP",
                    format="$%.2f",
                ),
            "gdp_per_capita_usd":
                st.column_config.NumberColumn(
                    "GDP / Capita",
                    format="$%.2f",
                ),
            "internet_users_pct":
                st.column_config.ProgressColumn(
                    "Internet Users",
                    min_value=0,
                    max_value=100,
                    format="%.2f%%",
                ),
            "ai_customer_adoption_pct":
                st.column_config.ProgressColumn(
                    "AI Adoption",
                    min_value=0,
                    max_value=100,
                    format="%.2f%%",
                ),
        },
    )


# ============================================================
# MARKET OPPORTUNITY
# ============================================================

def render_opportunity_ranking(
    opportunity: pd.DataFrame,
) -> None:

    st.subheader(
        "Global Market Opportunity Ranking"
    )

    data = opportunity.sort_values(
        "opportunity_rank",
        ascending=False,
    ).copy()

    fig = px.bar(
        data,
        x="market_opportunity_score",
        y="country_name",
        orientation="h",
        text="market_opportunity_score",
        hover_data={
            "country_code": True,
            "opportunity_rank": True,
            "opportunity_band": True,
            "gdp_score": ":.2f",
            "wealth_score": ":.2f",
            "digital_score": ":.2f",
            "whitespace_score": ":.2f",
            "customer_whitespace_score": ":.2f",
            "net_revenue_usd": ":,.2f",
        },
        labels={
            "market_opportunity_score":
                "Market Opportunity Score",
            "country_name":
                "Country",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
    )

    fig.update_layout(
        height=max(
            480,
            len(data) * 52,
        ),
        yaxis_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Market Opportunity Score",
        (
            "The Market Opportunity Score is a composite analytical score "
            "built from economic scale, wealth, digital readiness and "
            "commercial whitespace indicators in the semantic layer."
        ),
        (
            "Higher scores represent stronger relative opportunity according "
            "to the current scoring framework. Opportunity Rank 1 represents "
            "the highest-ranked market."
        ),
        (
            "The score gives strategy teams a consistent framework for "
            "comparing markets instead of evaluating each indicator in "
            "isolation."
        ),
        caution=(
            "This score is a prioritization model, not a guarantee of future "
            "sales or market success. Regulatory, competitive, product-fit "
            "and execution factors are not fully represented."
        ),
    )


def render_opportunity_components(
    opportunity: pd.DataFrame,
) -> None:

    st.subheader(
        "Opportunity Score Composition"
    )

    score_columns = [
        "gdp_score",
        "wealth_score",
        "digital_score",
        "whitespace_score",
        "customer_whitespace_score",
    ]

    data = opportunity[
        [
            "country_name",
            *score_columns,
        ]
    ].copy()

    data = data.set_index(
        "country_name"
    )

    data = data.rename(
        columns={
            "gdp_score":
                "GDP Score",
            "wealth_score":
                "Wealth Score",
            "digital_score":
                "Digital Score",
            "whitespace_score":
                "Revenue Whitespace",
            "customer_whitespace_score":
                "Customer Whitespace",
        }
    )

    fig = px.imshow(
        data,
        text_auto=True,
        aspect="auto",
        zmin=0,
        zmax=100,
        labels={
            "x": "Opportunity Dimension",
            "y": "Country",
            "color": "Score",
        },
    )

    fig.update_layout(
        height=max(
            500,
            len(data) * 52,
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Opportunity Score Composition",
        (
            "The heatmap breaks the overall opportunity score into its "
            "underlying analytical dimensions."
        ),
        (
            "A country may rank highly for different reasons. One market "
            "may have exceptional economic scale while another may have "
            "greater revenue or customer whitespace."
        ),
        (
            "Breaking apart the composite score prevents executives from "
            "treating a single ranking as a black box."
        ),
    )


def render_market_position_matrix(
    opportunity: pd.DataFrame,
) -> None:

    st.subheader(
        "Current Revenue vs Future Opportunity"
    )

    data = opportunity.copy()

    fig = px.scatter(
        data,
        x="net_revenue_usd",
        y="market_opportunity_score",
        size="gdp_usd",
        hover_name="country_name",
        hover_data={
            "opportunity_rank": True,
            "opportunity_band": True,
            "total_customers": ":,",
            "ai_customer_adoption_pct": ":.2f",
            "internet_users_pct": ":.2f",
            "gdp_per_capita_usd": ":,.2f",
            "whitespace_score": ":.2f",
            "customer_whitespace_score": ":.2f",
        },
        labels={
            "net_revenue_usd":
                "Current Nexus Revenue (USD)",
            "market_opportunity_score":
                "Market Opportunity Score",
        },
    )

    if not data.empty:

        fig.add_vline(
            x=data[
                "net_revenue_usd"
            ].median(),
            line_dash="dash",
        )

        fig.add_hline(
            y=data[
                "market_opportunity_score"
            ].median(),
            line_dash="dash",
        )

    fig.update_layout(
        height=560
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Current Revenue vs Future Opportunity",
        (
            "This matrix compares current commercial performance with the "
            "market opportunity score."
        ),
        (
            "Markets with high opportunity but lower current revenue may "
            "represent expansion whitespace. High-revenue, high-opportunity "
            "markets may justify continued strategic investment."
        ),
        (
            "This creates an executive portfolio view for geographic "
            "resource allocation."
        ),
    )


def render_opportunity_table(
    opportunity: pd.DataFrame,
) -> None:

    st.subheader(
        "Market Opportunity Detail"
    )

    columns = [
        "opportunity_rank",
        "country_code",
        "country_name",
        "total_customers",
        "ai_customers",
        "net_revenue_usd",
        "gdp_usd",
        "population",
        "gdp_per_capita_usd",
        "internet_users_pct",
        "inflation_pct",
        "ai_customer_adoption_pct",
        "gdp_score",
        "wealth_score",
        "digital_score",
        "whitespace_score",
        "customer_whitespace_score",
        "market_opportunity_score",
        "opportunity_band",
    ]

    data = opportunity[
        [
            column
            for column in columns
            if column in opportunity.columns
        ]
    ].sort_values(
        "opportunity_rank"
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "net_revenue_usd":
                st.column_config.NumberColumn(
                    "Revenue",
                    format="$%.2f",
                ),
            "gdp_usd":
                st.column_config.NumberColumn(
                    "GDP",
                    format="$%.2f",
                ),
            "gdp_per_capita_usd":
                st.column_config.NumberColumn(
                    "GDP / Capita",
                    format="$%.2f",
                ),
            "internet_users_pct":
                st.column_config.ProgressColumn(
                    "Internet Users",
                    min_value=0,
                    max_value=100,
                    format="%.2f%%",
                ),
            "ai_customer_adoption_pct":
                st.column_config.ProgressColumn(
                    "AI Adoption",
                    min_value=0,
                    max_value=100,
                    format="%.2f%%",
                ),
            "market_opportunity_score":
                st.column_config.ProgressColumn(
                    "Opportunity Score",
                    min_value=0,
                    max_value=100,
                    format="%.1f",
                ),
        },
    )


# ============================================================
# EXECUTIVE INSIGHTS
# ============================================================

def render_market_executive_insights(
    fx: pd.DataFrame,
    macro: pd.DataFrame,
    opportunity: pd.DataFrame,
) -> None:

    st.subheader(
        "Executive Market Signals"
    )

    if (
        fx.empty
        or macro.empty
        or opportunity.empty
    ):
        st.info(
            "Insufficient data for executive market insights."
        )
        return

    highest_exposure = fx.iloc[
        fx["revenue_exposure_pct"].argmax()
    ]

    highest_fx_risk = fx.iloc[
        fx["fx_risk_score"].argmax()
    ]

    top_revenue_country = macro.iloc[
        macro["net_revenue_usd"].argmax()
    ]

    top_opportunity = opportunity.sort_values(
        "opportunity_rank"
    ).iloc[0]

    lowest_ai_adoption = macro.iloc[
        macro[
            "ai_customer_adoption_pct"
        ].argmin()
    ]

    row1 = st.columns(3)

    with row1[0]:

        st.markdown(
            "#### Largest Currency Exposure"
        )

        st.write(
            f"**{highest_exposure['currency_code']} - "
            f"{highest_exposure['currency_name']}** represents "
            f"**{pct(highest_exposure['revenue_exposure_pct'])}** "
            f"of measured revenue exposure."
        )

    with row1[1]:

        st.markdown(
            "#### Highest FX Risk Signal"
        )

        st.write(
            f"**{highest_fx_risk['currency_code']}** has the "
            f"highest FX risk score at "
            f"**{decimal(highest_fx_risk['fx_risk_score'], 2)}**, "
            f"classified as **{highest_fx_risk['fx_risk_band']}**."
        )

    with row1[2]:

        st.markdown(
            "#### Largest Revenue Market"
        )

        st.write(
            f"**{top_revenue_country['country_name']}** is the "
            f"largest current revenue market at "
            f"**{money(top_revenue_country['net_revenue_usd'])}**."
        )

    row2 = st.columns(2)

    with row2[0]:

        st.markdown(
            "#### Top Expansion Opportunity"
        )

        st.write(
            f"**{top_opportunity['country_name']}** ranks #1 "
            f"with a market opportunity score of "
            f"**{decimal(top_opportunity['market_opportunity_score'], 1)}** "
            f"and is classified as "
            f"**{top_opportunity['opportunity_band']}**."
        )

    with row2[1]:

        st.markdown(
            "#### AI Adoption Whitespace Signal"
        )

        st.write(
            f"**{lowest_ai_adoption['country_name']}** currently has "
            f"the lowest AI customer adoption among the displayed markets "
            f"at **{pct(lowest_ai_adoption['ai_customer_adoption_pct'])}**."
        )

    st.markdown(
        "#### Strategic Priority Markets"
    )

    priority = opportunity.sort_values(
        "opportunity_rank"
    ).head(5)

    st.dataframe(
        priority[
            [
                "opportunity_rank",
                "country_name",
                "net_revenue_usd",
                "market_opportunity_score",
                "opportunity_band",
                "gdp_score",
                "digital_score",
                "whitespace_score",
                "customer_whitespace_score",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "These signals summarize the current semantic-layer data. "
        "They support management review but do not represent automated "
        "investment, treasury or geographic expansion decisions."
    )