from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def money(value: float) -> str:
    value = float(value or 0)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.2f}K"

    return f"${value:,.2f}"


def number(value: float) -> str:
    value = float(value or 0)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:,.1f}K"

    return f"{value:,.0f}"


def pct(value: float) -> str:
    return f"{float(value or 0):,.2f}%"


def section_explainer(
    title: str,
    definition: str,
    interpretation: str,
    business_use: str,
) -> None:
    with st.expander(f"ℹ️ Understanding {title}"):
        st.markdown(
            f"""
**What it means**

{definition}

**How to interpret it**

{interpretation}

**Why management cares**

{business_use}
"""
        )


def render_portfolio_kpis(
    ranking: pd.DataFrame,
    penetration: pd.DataFrame,
    ai: pd.DataFrame,
) -> None:

    total_revenue = ranking["revenue_usd"].sum()
    total_products = ranking["product_code"].nunique()

    avg_penetration = (
        penetration["customer_penetration_pct"].mean()
        if not penetration.empty
        else 0
    )

    weighted_ai_adoption = 0.0

    if not ai.empty and ai["customers"].sum() > 0:
        weighted_ai_adoption = (
            ai["ai_customers"].sum()
            / ai["customers"].sum()
            * 100
        )

    ai_revenue = (
        ai["ai_customer_revenue_usd"].sum()
        if not ai.empty
        else 0
    )

    cols = st.columns(5)

    cols[0].metric(
        "Portfolio Revenue",
        money(total_revenue),
    )

    cols[1].metric(
        "Products",
        f"{total_products:,}",
    )

    cols[2].metric(
        "Avg Product Penetration",
        pct(avg_penetration),
    )

    cols[3].metric(
        "AI Adoption",
        pct(weighted_ai_adoption),
    )

    cols[4].metric(
        "AI Customer Revenue",
        money(ai_revenue),
    )

    section_explainer(
        "Portfolio KPIs",
        (
            "Portfolio Revenue measures total revenue generated across the "
            "product portfolio. Product Penetration measures the percentage "
            "of the customer base using a product. AI Adoption measures the "
            "share of customers classified as AI customers."
        ),
        (
            "Revenue shows commercial scale, while penetration shows how "
            "widely products are adopted. A product can generate high revenue "
            "without broad penetration if a smaller number of large customers "
            "drive its sales."
        ),
        (
            "Executives can use these KPIs to balance revenue growth, "
            "customer adoption, product diversification and AI expansion."
        ),
    )


def render_revenue_leaderboard(
    ranking: pd.DataFrame,
) -> None:

    st.subheader("Product Revenue Leadership")

    data = (
        ranking
        .sort_values("revenue_usd", ascending=True)
        .copy()
    )

    fig = px.bar(
        data,
        x="revenue_usd",
        y="product_name",
        orientation="h",
        text="revenue_share_pct",
        hover_data={
            "product_code": True,
            "product_family": True,
            "customers": ":,",
            "transactions": ":,",
            "revenue_rank": True,
            "revenue_usd": ":,.2f",
            "revenue_share_pct": ":.2f",
        },
        labels={
            "revenue_usd": "Revenue (USD)",
            "product_name": "Product",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(
        height=max(420, len(data) * 45),
        yaxis_title="",
        xaxis_title="Revenue (USD)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Product Revenue Leadership",
        (
            "This chart ranks products according to the revenue they generate. "
            "Revenue Share represents each product's contribution to total "
            "portfolio revenue."
        ),
        (
            "Products near the top are the largest commercial contributors. "
            "A very concentrated portfolio means business performance may "
            "depend heavily on a small number of products."
        ),
        (
            "Product leaders can use this ranking for investment allocation, "
            "pricing strategy, sales prioritisation and portfolio risk analysis."
        ),
    )


def render_penetration_chart(
    penetration: pd.DataFrame,
) -> None:

    st.subheader("Customer Product Penetration")

    data = penetration.sort_values(
        "customer_penetration_pct",
        ascending=True,
    )

    fig = px.bar(
        data,
        x="customer_penetration_pct",
        y="product_name",
        orientation="h",
        hover_data={
            "service_category": True,
            "is_ai_service": True,
            "customers_using_product": ":,",
            "total_customer_base": ":,",
            "product_revenue_usd": ":,.2f",
            "penetration_rank": True,
        },
        labels={
            "customer_penetration_pct": "Customer Penetration (%)",
            "product_name": "Product",
        },
    )

    fig.update_layout(
        height=max(420, len(data) * 45),
        yaxis_title="",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Product Penetration",
        (
            "Customer Penetration is the percentage of the total customer "
            "base that currently uses each product."
        ),
        (
            "High penetration indicates broad adoption. Low penetration does "
            "not automatically mean poor performance; it may represent an "
            "important cross-sell opportunity."
        ),
        (
            "Sales and product teams can identify products with substantial "
            "remaining whitespace inside the existing customer base."
        ),
    )


def render_revenue_penetration_matrix(
    penetration: pd.DataFrame,
) -> None:

    st.subheader("Revenue vs Customer Penetration")

    data = penetration.copy()

    fig = px.scatter(
        data,
        x="customer_penetration_pct",
        y="product_revenue_usd",
        size="customers_using_product",
        hover_name="product_name",
        hover_data={
            "product_code": True,
            "product_family": True,
            "service_category": True,
            "is_ai_service": True,
            "customers_using_product": ":,",
            "product_revenue_usd": ":,.2f",
        },
        labels={
            "customer_penetration_pct": "Customer Penetration (%)",
            "product_revenue_usd": "Product Revenue (USD)",
        },
    )

    if not data.empty:
        avg_penetration = data[
            "customer_penetration_pct"
        ].mean()

        avg_revenue = data[
            "product_revenue_usd"
        ].mean()

        fig.add_vline(
            x=avg_penetration,
            line_dash="dash",
        )

        fig.add_hline(
            y=avg_revenue,
            line_dash="dash",
        )

    fig.update_layout(height=520)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "Revenue vs Customer Penetration Matrix",
        (
            "The matrix compares commercial value with adoption. The "
            "horizontal axis measures customer penetration and the vertical "
            "axis measures product revenue."
        ),
        (
            "Upper-right products combine strong revenue with broad adoption. "
            "Upper-left products generate strong revenue despite relatively "
            "lower penetration and may offer attractive expansion potential. "
            "Lower-left products require deeper investigation."
        ),
        (
            "This is useful for product portfolio strategy because it separates "
            "commercial strength from adoption strength."
        ),
    )


def render_ai_adoption_by_segment(
    ai: pd.DataFrame,
) -> None:

    st.subheader("AI Adoption by Customer Segment")

    grouped = (
        ai.groupby("customer_segment", as_index=False)
        .agg(
            customers=("customers", "sum"),
            ai_customers=("ai_customers", "sum"),
        )
    )

    grouped["ai_adoption_pct"] = (
        grouped["ai_customers"]
        / grouped["customers"].replace(0, pd.NA)
        * 100
    ).fillna(0)

    grouped = grouped.sort_values(
        "ai_adoption_pct",
        ascending=False,
    )

    fig = px.bar(
        grouped,
        x="customer_segment",
        y="ai_adoption_pct",
        text="ai_adoption_pct",
        hover_data={
            "customers": ":,",
            "ai_customers": ":,",
        },
        labels={
            "customer_segment": "Customer Segment",
            "ai_adoption_pct": "AI Adoption (%)",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(height=440)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "AI Adoption",
        (
            "AI Adoption measures the proportion of customers within each "
            "segment that are classified as AI customers."
        ),
        (
            "Higher percentages indicate stronger AI penetration. Lower "
            "adoption segments represent possible enablement, education, "
            "migration or cross-sell opportunities."
        ),
        (
            "Leadership can identify where AI adoption is strongest and where "
            "additional go-to-market investment may create growth."
        ),
    )


def render_ai_industry_heatmap(
    ai: pd.DataFrame,
) -> None:

    st.subheader("AI Adoption Heatmap")

    pivot = ai.pivot_table(
        index="industry",
        columns="customer_segment",
        values="ai_adoption_pct",
        aggfunc="mean",
    )

    if pivot.empty:
        st.info("No AI adoption data available.")
        return

    fig = px.imshow(
        pivot,
        text_auto=True,
        aspect="auto",
        labels={
            "x": "Customer Segment",
            "y": "Industry",
            "color": "AI Adoption %",
        },
    )

    fig.update_layout(
        height=max(450, len(pivot) * 45),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "AI Adoption Heatmap",
        (
            "The heatmap compares AI adoption across combinations of industry "
            "and customer segment."
        ),
        (
            "Higher cells represent stronger AI penetration. Lower cells "
            "highlight areas where AI adoption is relatively underdeveloped."
        ),
        (
            "This helps account teams identify specific industry-segment "
            "combinations for targeted AI campaigns instead of using a "
            "one-size-fits-all strategy."
        ),
    )


def render_ai_economics(
    ai: pd.DataFrame,
) -> None:

    st.subheader("AI Customer Revenue Economics")

    grouped = (
        ai.groupby("customer_segment", as_index=False)
        .agg(
            customers=("customers", "sum"),
            ai_customers=("ai_customers", "sum"),
            ai_customer_revenue_usd=(
                "ai_customer_revenue_usd",
                "sum",
            ),
            ai_customer_gross_profit_usd=(
                "ai_customer_gross_profit_usd",
                "sum",
            ),
        )
    )

    grouped["ai_gross_margin_pct"] = (
        grouped["ai_customer_gross_profit_usd"]
        / grouped["ai_customer_revenue_usd"].replace(
            0,
            pd.NA,
        )
        * 100
    ).fillna(0)

    fig = px.bar(
        grouped,
        x="customer_segment",
        y="ai_customer_revenue_usd",
        text="ai_gross_margin_pct",
        hover_data={
            "customers": ":,",
            "ai_customers": ":,",
            "ai_customer_gross_profit_usd": ":,.2f",
            "ai_gross_margin_pct": ":.2f",
        },
        labels={
            "customer_segment": "Customer Segment",
            "ai_customer_revenue_usd": "AI Customer Revenue (USD)",
        },
    )

    fig.update_traces(
        texttemplate="Margin %{text:.1f}%",
        textposition="outside",
    )

    fig.update_layout(height=460)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    section_explainer(
        "AI Revenue Economics",
        (
            "AI Customer Revenue measures revenue associated with customers "
            "classified as AI customers. AI Gross Margin compares their gross "
            "profit with AI customer revenue."
        ),
        (
            "Revenue measures scale while gross margin indicates the quality "
            "of that revenue. High growth with weak margins can require cost "
            "optimisation."
        ),
        (
            "Executives can assess whether AI adoption is translating into "
            "commercially attractive and profitable customer relationships."
        ),
    )


def render_ai_customer_value_comparison(
    ai: pd.DataFrame,
) -> None:

    st.subheader("AI vs Non-AI Customer Revenue")

    data = ai.copy()

    weighted_ai = (
        (
            data["avg_ai_customer_revenue_usd"]
            * data["ai_customers"]
        ).sum()
        / data["ai_customers"].sum()
        if data["ai_customers"].sum() > 0
        else 0
    )

    non_ai_customers = (
        data["customers"] - data["ai_customers"]
    ).clip(lower=0)

    weighted_non_ai = (
        (
            data["avg_non_ai_customer_revenue_usd"]
            * non_ai_customers
        ).sum()
        / non_ai_customers.sum()
        if non_ai_customers.sum() > 0
        else 0
    )

    comparison = pd.DataFrame(
        {
            "Customer Type": [
                "AI Customer",
                "Non-AI Customer",
            ],
            "Average Revenue": [
                weighted_ai,
                weighted_non_ai,
            ],
        }
    )

    fig = px.bar(
        comparison,
        x="Customer Type",
        y="Average Revenue",
        text="Average Revenue",
        labels={
            "Average Revenue": "Average Revenue (USD)",
        },
    )

    fig.update_traces(
        texttemplate="$%{text:,.0f}",
        textposition="outside",
    )

    fig.update_layout(height=430)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    difference = weighted_ai - weighted_non_ai

    if weighted_non_ai:
        uplift = (
            difference / weighted_non_ai * 100
        )
    else:
        uplift = 0

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Avg AI Customer Revenue",
        money(weighted_ai),
    )

    c2.metric(
        "Avg Non-AI Customer Revenue",
        money(weighted_non_ai),
    )

    c3.metric(
        "AI Revenue Difference",
        money(difference),
        delta=f"{uplift:.2f}%",
    )

    section_explainer(
        "AI vs Non-AI Customer Revenue",
        (
            "This comparison evaluates the average revenue associated with AI "
            "customers against non-AI customers."
        ),
        (
            "A positive difference means AI customers generate more revenue "
            "on average. A negative difference means AI adoption is not yet "
            "associated with higher average customer revenue in the current "
            "dataset."
        ),
        (
            "This provides evidence for evaluating AI monetisation rather than "
            "assuming that AI adoption automatically creates higher-value "
            "customers."
        ),
    )


def render_product_table(
    penetration: pd.DataFrame,
) -> None:

    st.subheader("Product Portfolio Detail")

    columns = [
        "penetration_rank",
        "product_code",
        "product_name",
        "product_family",
        "service_category",
        "is_ai_service",
        "customers_using_product",
        "total_customer_base",
        "customer_penetration_pct",
        "product_revenue_usd",
    ]

    data = penetration[
        [c for c in columns if c in penetration.columns]
    ].copy()

    data = data.sort_values(
        "penetration_rank",
    )

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "product_revenue_usd": st.column_config.NumberColumn(
                "Product Revenue",
                format="$%.2f",
            ),
            "customer_penetration_pct": st.column_config.ProgressColumn(
                "Customer Penetration",
                min_value=0,
                max_value=100,
                format="%.2f%%",
            ),
            "is_ai_service": st.column_config.CheckboxColumn(
                "AI Service",
            ),
        },
    )


def render_ai_opportunity_table(
    ai: pd.DataFrame,
) -> None:

    st.subheader("AI Expansion Opportunity")

    data = ai.copy()

    data["non_ai_customers"] = (
        data["customers"] - data["ai_customers"]
    ).clip(lower=0)

    data["ai_revenue_share_pct"] = (
        data["ai_customer_revenue_usd"]
        / data["total_revenue_usd"].replace(0, pd.NA)
        * 100
    ).fillna(0)

    data["ai_gross_margin_pct"] = (
        data["ai_customer_gross_profit_usd"]
        / data["ai_customer_revenue_usd"].replace(
            0,
            pd.NA,
        )
        * 100
    ).fillna(0)

    data = data.sort_values(
        [
            "non_ai_customers",
            "total_revenue_usd",
        ],
        ascending=[False, False],
    )

    display_columns = [
        "customer_segment",
        "industry",
        "customers",
        "ai_customers",
        "non_ai_customers",
        "ai_adoption_pct",
        "total_revenue_usd",
        "ai_customer_revenue_usd",
        "ai_revenue_share_pct",
        "ai_gross_margin_pct",
    ]

    st.dataframe(
        data[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "ai_adoption_pct": st.column_config.ProgressColumn(
                "AI Adoption",
                min_value=0,
                max_value=100,
                format="%.2f%%",
            ),
            "total_revenue_usd": st.column_config.NumberColumn(
                "Total Revenue",
                format="$%.2f",
            ),
            "ai_customer_revenue_usd": st.column_config.NumberColumn(
                "AI Revenue",
                format="$%.2f",
            ),
            "ai_revenue_share_pct": st.column_config.NumberColumn(
                "AI Revenue Share",
                format="%.2f%%",
            ),
            "ai_gross_margin_pct": st.column_config.NumberColumn(
                "AI Gross Margin",
                format="%.2f%%",
            ),
        },
    )

    section_explainer(
        "AI Expansion Opportunity",
        (
            "Non-AI Customers represents the remaining customer population "
            "within each industry and segment that has not yet been classified "
            "as AI adopted."
        ),
        (
            "Large customer populations combined with relatively low AI "
            "adoption indicate potential whitespace. This should be treated as "
            "an opportunity signal, not as a guaranteed sales forecast."
        ),
        (
            "Sales teams can use the table to prioritise market segments for "
            "AI education, pilots, cross-sell campaigns and account planning."
        ),
    )