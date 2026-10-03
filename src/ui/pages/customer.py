from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.ui.components.customer import (
    format_currency,
    format_number,
    format_percent,
    render_customer_cloud,
    render_customer_commercial_value,
    render_customer_identity,
    render_customer_risk,
    render_customer_subscription,
    render_customer_support,
)
from src.ui.components.insight import (
    render_chart_guide,
    render_insight_panel,
    render_metric_dictionary,
)
from src.ui.components.kpi import render_kpi
from src.ui.data_service import load_customer_bundle
from src.ui.theme import render_page_header


# ============================================================
# HELPERS
# ============================================================


def _layout(
    figure,
    height: int = 420,
):
    """
    Shared Plotly layout for Nexus360.
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


def _numeric(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:

    if column not in dataframe.columns:
        return pd.Series(
            dtype="float64"
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )


def _safe_sum(
    dataframe: pd.DataFrame,
    column: str,
) -> float:

    values = _numeric(
        dataframe,
        column,
    )

    if values.empty:
        return 0.0

    return float(
        values.fillna(0).sum()
    )


def _safe_mean(
    dataframe: pd.DataFrame,
    column: str,
) -> float:

    values = _numeric(
        dataframe,
        column,
    ).dropna()

    if values.empty:
        return 0.0

    return float(
        values.mean()
    )


# ============================================================
# PORTFOLIO OVERVIEW
# ============================================================


def _render_portfolio(
    customer_360: pd.DataFrame,
    value_tiers: pd.DataFrame,
    risk: pd.DataFrame,
) -> None:

    st.subheader(
        "Customer Portfolio"
    )

    st.caption(
        "Executive view of customer scale, value, AI adoption "
        "and modeled commercial exposure."
    )

    total_customers = (
        customer_360["customer_id"].nunique()
        if "customer_id" in customer_360.columns
        else len(customer_360)
    )

    total_revenue = _safe_sum(
        customer_360,
        "lifetime_revenue_usd",
    )

    ai_customers = 0

    if "is_ai_customer" in customer_360.columns:
        ai_customers = int(
            customer_360[
                "is_ai_customer"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

    ai_adoption = (
        ai_customers
        / total_customers
        * 100
        if total_customers > 0
        else 0
    )

    revenue_at_risk = _safe_sum(
        risk,
        "revenue_at_risk_usd",
    )

    kpis = st.columns(
        4,
        gap="medium",
    )

    with kpis[0]:
        render_kpi(
            "Customers",
            total_customers,
            kind="number",
            detail="Customer portfolio size",
            sentiment="neutral",
        )

    with kpis[1]:
        render_kpi(
            "Lifetime Revenue",
            total_revenue,
            kind="currency",
            detail="Revenue represented by customers",
            sentiment="positive",
        )

    with kpis[2]:
        render_kpi(
            "AI Adoption",
            ai_adoption,
            kind="percent",
            detail="Customers using AI services",
            sentiment="positive",
        )

    with kpis[3]:
        render_kpi(
            "Revenue at Risk",
            revenue_at_risk,
            kind="currency",
            detail="Modeled commercial exposure",
            sentiment="negative",
        )

    left, right = st.columns(
        2,
        gap="large",
    )

    # --------------------------------------------------------
    # CUSTOMER SEGMENT
    # --------------------------------------------------------

    with left:

        st.markdown(
            "### Customer Segment Mix"
        )

        if (
            "customer_segment"
            in customer_360.columns
        ):

            segment_data = (
                customer_360[
                    "customer_segment"
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "Customer Segment"
                )
                .reset_index(
                    name="Customers"
                )
            )

            figure = px.bar(
                segment_data,
                x="Customer Segment",
                y="Customers",
                labels={
                    "Customers":
                        "Number of Customers",
                },
            )

            _layout(
                figure,
                390,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

            render_chart_guide(
                title="Customer Segment Mix",
                definition=(
                    "Shows how the customer portfolio is "
                    "distributed across commercial segments."
                ),
                business_question=(
                    "Which customer segments dominate the "
                    "portfolio?"
                ),
                interpretation=[
                    (
                        "Higher bars indicate a larger customer "
                        "population within that segment."
                    ),
                    (
                        "Customer count should be interpreted "
                        "alongside revenue and profitability; "
                        "the largest segment is not necessarily "
                        "the most valuable."
                    ),
                ],
                business_use=[
                    "Sales coverage planning.",
                    "Segment strategy.",
                    "Customer portfolio analysis.",
                ],
            )

    # --------------------------------------------------------
    # VALUE TIERS
    # --------------------------------------------------------

    with right:

        st.markdown(
            "### Customer Value Tiers"
        )

        if (
            "customer_value_tier"
            in value_tiers.columns
        ):

            tier_data = (
                value_tiers[
                    "customer_value_tier"
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "Value Tier"
                )
                .reset_index(
                    name="Customers"
                )
            )

            figure = px.pie(
                tier_data,
                names="Value Tier",
                values="Customers",
                hole=0.58,
            )

            _layout(
                figure,
                390,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

            render_chart_guide(
                title="Customer Value Tiers",
                definition=(
                    "Groups customers into value tiers based "
                    "on the semantic-layer customer value model."
                ),
                business_question=(
                    "How is commercial value distributed across "
                    "the customer base?"
                ),
                interpretation=[
                    (
                        "Higher-value tiers represent customers "
                        "with stronger lifetime commercial value."
                    ),
                    (
                        "Tiering supports differentiated service, "
                        "retention and account-management strategies."
                    ),
                ],
                business_use=[
                    "Account prioritization.",
                    "Retention strategy.",
                    "Customer success allocation.",
                ],
            )


# ============================================================
# RFM
# ============================================================


def _render_rfm(
    rfm: pd.DataFrame,
) -> None:

    st.divider()

    st.subheader(
        "RFM Customer Intelligence"
    )

    st.caption(
        "Recency, Frequency and Monetary analysis segments "
        "customers according to purchasing behavior."
    )

    if rfm.empty:
        st.warning(
            "RFM dataset is unavailable."
        )
        return

    left, right = st.columns(
        [1, 1.4],
        gap="large",
    )

    with left:

        if "rfm_segment" in rfm.columns:

            segment_data = (
                rfm[
                    "rfm_segment"
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "RFM Segment"
                )
                .reset_index(
                    name="Customers"
                )
            )

            figure = px.bar(
                segment_data,
                x="Customers",
                y="RFM Segment",
                orientation="h",
            )

            figure.update_layout(
                yaxis={
                    "categoryorder": "total ascending"
                }
            )

            _layout(
                figure,
                430,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

    with right:

        required = {
            "recency_days",
            "purchase_frequency",
            "monetary_value",
            "rfm_segment",
        }

        if required.issubset(
            rfm.columns
        ):

            scatter = rfm[
                [
                    "customer_id",
                    "customer_name",
                    "recency_days",
                    "purchase_frequency",
                    "monetary_value",
                    "rfm_segment",
                ]
            ].copy()

            scatter[
                "recency_days"
            ] = pd.to_numeric(
                scatter["recency_days"],
                errors="coerce",
            )

            scatter[
                "purchase_frequency"
            ] = pd.to_numeric(
                scatter[
                    "purchase_frequency"
                ],
                errors="coerce",
            )

            scatter[
                "monetary_value"
            ] = pd.to_numeric(
                scatter["monetary_value"],
                errors="coerce",
            )

            scatter = scatter.dropna(
                subset=[
                    "recency_days",
                    "purchase_frequency",
                    "monetary_value",
                ]
            )

            figure = px.scatter(
                scatter,
                x="recency_days",
                y="purchase_frequency",
                size="monetary_value",
                color="rfm_segment",
                hover_name="customer_name",
                hover_data=[
                    "customer_id",
                    "monetary_value",
                ],
                labels={
                    "recency_days":
                        "Recency (Days)",
                    "purchase_frequency":
                        "Purchase Frequency",
                    "monetary_value":
                        "Monetary Value",
                    "rfm_segment":
                        "RFM Segment",
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
        title="RFM Customer Intelligence",
        definition=(
            "RFM evaluates customers using Recency, Frequency "
            "and Monetary Value."
        ),
        business_question=(
            "Which customers are highly engaged, valuable, "
            "inactive or potentially in need of re-engagement?"
        ),
        interpretation=[
            (
                "Recency measures how long it has been since "
                "the customer's latest purchase. Lower recency "
                "is generally more recent."
            ),
            (
                "Frequency measures how often the customer "
                "has purchased."
            ),
            (
                "Monetary value measures total customer revenue "
                "represented in the RFM model."
            ),
            (
                "The RFM segment converts these behavioral "
                "signals into a more interpretable category."
            ),
        ],
        business_use=[
            "Retention campaigns.",
            "Customer prioritization.",
            "Re-engagement targeting.",
            "Commercial segmentation.",
        ],
        caveat=(
            "RFM is behavioral segmentation. It does not itself "
            "prove customer satisfaction, loyalty or future churn."
        ),
    )


# ============================================================
# PARETO
# ============================================================


def _render_pareto(
    pareto: pd.DataFrame,
) -> None:

    st.divider()

    st.subheader(
        "Customer Revenue Concentration — Pareto Analysis"
    )

    st.caption(
        "Evaluates whether a relatively small share of customers "
        "contributes a disproportionate share of revenue."
    )

    required = {
        "cumulative_customer_pct",
        "cumulative_revenue_pct",
    }

    if not required.issubset(
        pareto.columns
    ):
        st.warning(
            "Pareto dataset does not contain the required columns."
        )
        return

    chart = pareto.copy()

    chart[
        "cumulative_customer_pct"
    ] = pd.to_numeric(
        chart["cumulative_customer_pct"],
        errors="coerce",
    )

    chart[
        "cumulative_revenue_pct"
    ] = pd.to_numeric(
        chart["cumulative_revenue_pct"],
        errors="coerce",
    )

    chart = chart.dropna(
        subset=[
            "cumulative_customer_pct",
            "cumulative_revenue_pct",
        ]
    ).sort_values(
        "cumulative_customer_pct"
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=chart[
                "cumulative_customer_pct"
            ],
            y=chart[
                "cumulative_revenue_pct"
            ],
            mode="lines",
            name="Cumulative Revenue",
        )
    )

    figure.add_shape(
        type="line",
        x0=0,
        y0=80,
        x1=100,
        y1=80,
        line=dict(
            dash="dash",
        ),
    )

    figure.update_xaxes(
        title="Cumulative Customers (%)"
    )

    figure.update_yaxes(
        title="Cumulative Revenue (%)"
    )

    _layout(
        figure,
        430,
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )

    # Determine customer share producing 80% revenue.

    eighty = chart[
        chart[
            "cumulative_revenue_pct"
        ] >= 80
    ]

    if not eighty.empty:

        customer_share = float(
            eighty.iloc[0][
                "cumulative_customer_pct"
            ]
        )

        render_insight_panel(
            metric=(
                "Cumulative revenue concentration"
            ),
            insight=(
                f"Approximately {customer_share:,.2f}% "
                "of customers account for the first 80% "
                "of cumulative revenue in the Pareto model."
            ),
            potential_action=(
                "Review concentration alongside customer risk. "
                "High revenue dependence on a limited number of "
                "accounts can increase commercial exposure."
            ),
        )

    render_chart_guide(
        title="Customer Pareto Analysis",
        definition=(
            "Ranks customers by revenue and compares cumulative "
            "customer share with cumulative revenue share."
        ),
        business_question=(
            "How concentrated is enterprise revenue across "
            "the customer portfolio?"
        ),
        interpretation=[
            (
                "A steep curve means revenue is concentrated "
                "among relatively few customers."
            ),
            (
                "A flatter curve indicates a more diversified "
                "customer revenue base."
            ),
            (
                "The 80% reference line helps evaluate the "
                "classic Pareto concentration pattern."
            ),
        ],
        business_use=[
            "Key-account strategy.",
            "Revenue concentration monitoring.",
            "Retention prioritization.",
        ],
    )


# ============================================================
# COHORT
# ============================================================


def _render_cohort(
    cohort: pd.DataFrame,
) -> None:

    st.divider()

    st.subheader(
        "Customer Cohort Retention"
    )

    st.caption(
        "Tracks customer activity over time based on signup cohort."
    )

    required = {
        "cohort_month",
        "months_since_signup",
        "retention_pct",
    }

    if not required.issubset(
        cohort.columns
    ):
        st.warning(
            "Cohort dataset does not contain the required columns."
        )
        return

    data = cohort.copy()

    data[
        "cohort_month"
    ] = pd.to_datetime(
        data["cohort_month"],
        errors="coerce",
    )

    data[
        "months_since_signup"
    ] = pd.to_numeric(
        data["months_since_signup"],
        errors="coerce",
    )

    data[
        "retention_pct"
    ] = pd.to_numeric(
        data["retention_pct"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "cohort_month",
            "months_since_signup",
            "retention_pct",
        ]
    )

    data[
        "Cohort"
    ] = data[
        "cohort_month"
    ].dt.strftime(
        "%Y-%m"
    )

    pivot = data.pivot_table(
        index="Cohort",
        columns="months_since_signup",
        values="retention_pct",
        aggfunc="mean",
    )

    if not pivot.empty:

        figure = px.imshow(
            pivot,
            aspect="auto",
            labels={
                "x":
                    "Months Since Signup",
                "y":
                    "Signup Cohort",
                "color":
                    "Retention %",
            },
        )

        figure.update_layout(
            height=max(
                480,
                min(
                    900,
                    220 + len(pivot) * 18,
                ),
            )
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

    render_chart_guide(
        title="Customer Cohort Retention",
        definition=(
            "Groups customers by signup month and measures the "
            "percentage remaining active at later month offsets."
        ),
        business_question=(
            "How does customer retention evolve after acquisition, "
            "and are some signup cohorts performing better?"
        ),
        interpretation=[
            (
                "Each row represents a signup cohort."
            ),
            (
                "Each column represents elapsed months since "
                "signup."
            ),
            (
                "Higher retention percentages indicate that a "
                "larger share of the original cohort remains active."
            ),
        ],
        business_use=[
            "Retention strategy.",
            "Acquisition-quality analysis.",
            "Lifecycle management.",
        ],
        caveat=(
            "Retention depends on the project's definition of "
            "customer activity in the semantic layer."
        ),
    )


# ============================================================
# SUBSCRIPTION HEALTH
# ============================================================


def _render_subscription_health(
    subscriptions: pd.DataFrame,
) -> None:

    st.divider()

    st.subheader(
        "Subscription Health"
    )

    st.caption(
        "Product-level subscription activity, contract value "
        "and auto-renew behavior."
    )

    if subscriptions.empty:
        st.warning(
            "Subscription health dataset is unavailable."
        )
        return

    total_subscriptions = _safe_sum(
        subscriptions,
        "total_subscriptions",
    )

    active_subscriptions = _safe_sum(
        subscriptions,
        "active_subscriptions",
    )

    active_contract_value = _safe_sum(
        subscriptions,
        "active_contract_value_usd",
    )

    auto_renew_subscriptions = _safe_sum(
        subscriptions,
        "auto_renew_subscriptions",
    )

    active_rate = (
        active_subscriptions
        / total_subscriptions
        * 100
        if total_subscriptions > 0
        else 0
    )

    auto_renew_rate = (
        auto_renew_subscriptions
        / total_subscriptions
        * 100
        if total_subscriptions > 0
        else 0
    )

    columns = st.columns(
        4,
        gap="medium",
    )

    with columns[0]:
        render_kpi(
            "Subscriptions",
            total_subscriptions,
            kind="number",
            detail="Total subscription records",
            sentiment="neutral",
        )

    with columns[1]:
        render_kpi(
            "Active Rate",
            active_rate,
            kind="percent",
            detail="Currently active subscriptions",
            sentiment="positive",
        )

    with columns[2]:
        render_kpi(
            "Auto-Renew Rate",
            auto_renew_rate,
            kind="percent",
            detail="Subscriptions configured for renewal",
            sentiment="positive",
        )

    with columns[3]:
        render_kpi(
            "Active Contract Value",
            active_contract_value,
            kind="currency",
            detail="Value of active subscriptions",
            sentiment="positive",
        )

    required = {
        "product_name",
        "active_subscription_pct",
        "auto_renew_pct",
    }

    if required.issubset(
        subscriptions.columns
    ):

        chart = subscriptions[
            [
                "product_name",
                "active_subscription_pct",
                "auto_renew_pct",
            ]
        ].copy()

        chart[
            "active_subscription_pct"
        ] = pd.to_numeric(
            chart[
                "active_subscription_pct"
            ],
            errors="coerce",
        )

        chart[
            "auto_renew_pct"
        ] = pd.to_numeric(
            chart[
                "auto_renew_pct"
            ],
            errors="coerce",
        )

        chart = chart.melt(
            id_vars="product_name",
            value_vars=[
                "active_subscription_pct",
                "auto_renew_pct",
            ],
            var_name="Metric",
            value_name="Percentage",
        )

        chart["Metric"] = chart[
            "Metric"
        ].replace(
            {
                "active_subscription_pct":
                    "Active Subscription %",
                "auto_renew_pct":
                    "Auto-Renew %",
            }
        )

        figure = px.bar(
            chart,
            x="product_name",
            y="Percentage",
            color="Metric",
            barmode="group",
            labels={
                "product_name":
                    "Product",
            },
        )

        _layout(
            figure,
            440,
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

    render_chart_guide(
        title="Subscription Health",
        definition=(
            "Compares subscription activity and auto-renew "
            "behavior across products."
        ),
        business_question=(
            "Which products have stronger active subscription "
            "and renewal profiles?"
        ),
        interpretation=[
            (
                "Active Subscription % measures the share of "
                "subscriptions currently classified as active."
            ),
            (
                "Auto-Renew % measures the share configured "
                "for automatic renewal."
            ),
            (
                "Auto-renew configuration is not equivalent "
                "to guaranteed future renewal."
            ),
        ],
        business_use=[
            "Subscription portfolio management.",
            "Renewal planning.",
            "Product health monitoring.",
        ],
    )


# ============================================================
# RENEWAL RISK
# ============================================================


def _render_renewal_risk(
    renewal: pd.DataFrame,
) -> None:

    st.divider()

    st.subheader(
        "Subscription Renewal Risk"
    )

    st.caption(
        "Analytical prioritization of subscriptions according "
        "to the Nexus360 renewal-risk methodology."
    )

    if renewal.empty:
        st.warning(
            "Renewal risk dataset is unavailable."
        )
        return

    left, right = st.columns(
        [1, 1.7],
        gap="large",
    )

    with left:

        if (
            "renewal_risk_band"
            in renewal.columns
        ):

            risk_distribution = (
                renewal[
                    "renewal_risk_band"
                ]
                .fillna("Unknown")
                .value_counts()
                .rename_axis(
                    "Risk Band"
                )
                .reset_index(
                    name="Subscriptions"
                )
            )

            figure = px.pie(
                risk_distribution,
                names="Risk Band",
                values="Subscriptions",
                hole=0.58,
            )

            _layout(
                figure,
                390,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

    with right:

        display = renewal.copy()

        if (
            "renewal_risk_score"
            in display.columns
        ):

            display[
                "renewal_risk_score"
            ] = pd.to_numeric(
                display[
                    "renewal_risk_score"
                ],
                errors="coerce",
            )

            display = display.sort_values(
                "renewal_risk_score",
                ascending=False,
            )

        columns = [
            column
            for column in [
                "subscription_id",
                "customer_id",
                "customer_name",
                "customer_segment",
                "product_name",
                "contract_value_usd",
                "subscription_status",
                "auto_renew",
                "renewal_risk_score",
                "renewal_risk_band",
            ]
            if column in display.columns
        ]

        st.markdown(
            "**Highest Renewal-Risk Subscriptions**"
        )

        st.dataframe(
            display[
                columns
            ].head(20),
            width="stretch",
            hide_index=True,
        )

    render_chart_guide(
        title="Subscription Renewal Risk",
        definition=(
            "Scores subscriptions using the Nexus360 analytical "
            "renewal-risk logic."
        ),
        business_question=(
            "Which subscriptions should be investigated first "
            "for potential renewal intervention?"
        ),
        interpretation=[
            (
                "Higher risk scores indicate stronger risk "
                "signals according to the project's model."
            ),
            (
                "Risk bands simplify prioritization into "
                "business-friendly groups."
            ),
            (
                "Risk is an analytical signal rather than a "
                "confirmed future cancellation."
            ),
        ],
        business_use=[
            "Renewal pipeline prioritization.",
            "Customer-success intervention.",
            "Account review.",
        ],
        caveat=(
            "The current renewal-risk score is a project analytical "
            "model. A later predictive-ML phase will independently "
            "evaluate probabilistic churn/renewal models."
        ),
    )


# ============================================================
# REVENUE AT RISK
# ============================================================


def _render_revenue_risk(
    risk: pd.DataFrame,
) -> None:

    st.divider()

    st.subheader(
        "Revenue at Risk"
    )

    st.caption(
        "Combines customer commercial value and risk signals "
        "to prioritize modeled revenue exposure."
    )

    if risk.empty:
        st.warning(
            "Revenue-at-risk dataset is unavailable."
        )
        return

    data = risk.copy()

    for column in [
        "lifetime_revenue_usd",
        "composite_risk_score",
        "revenue_at_risk_usd",
    ]:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

    if (
        "revenue_at_risk_usd"
        in data.columns
    ):
        data = data.sort_values(
            "revenue_at_risk_usd",
            ascending=False,
        )

    left, right = st.columns(
        [1.2, 1.8],
        gap="large",
    )

    with left:

        required = {
            "lifetime_revenue_usd",
            "composite_risk_score",
            "revenue_at_risk_usd",
        }

        if required.issubset(
            data.columns
        ):

            figure = px.scatter(
                data,
                x="composite_risk_score",
                y="lifetime_revenue_usd",
                size="revenue_at_risk_usd",
                color=(
                    "revenue_risk_band"
                    if "revenue_risk_band"
                    in data.columns
                    else None
                ),
                hover_name=(
                    "customer_name"
                    if "customer_name"
                    in data.columns
                    else None
                ),
                hover_data=[
                    column
                    for column in [
                        "customer_id",
                        "revenue_at_risk_usd",
                    ]
                    if column in data.columns
                ],
                labels={
                    "composite_risk_score":
                        "Composite Risk Score",
                    "lifetime_revenue_usd":
                        "Lifetime Revenue (USD)",
                    "revenue_at_risk_usd":
                        "Revenue at Risk (USD)",
                },
            )

            _layout(
                figure,
                440,
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

    with right:

        columns = [
            column
            for column in [
                "revenue_at_risk_rank",
                "customer_id",
                "customer_name",
                "customer_segment",
                "industry",
                "lifetime_revenue_usd",
                "renewal_risk_score",
                "sla_compliance_pct",
                "request_failure_rate_pct",
                "composite_risk_score",
                "revenue_at_risk_usd",
                "revenue_risk_band",
            ]
            if column in data.columns
        ]

        st.markdown(
            "**Commercial Exposure Ranking**"
        )

        st.dataframe(
            data[
                columns
            ].head(25),
            width="stretch",
            hide_index=True,
        )

    render_chart_guide(
        title="Revenue at Risk",
        definition=(
            "Estimates the commercial value associated with "
            "customers displaying elevated risk signals."
        ),
        business_question=(
            "Where should commercial-risk investigation be "
            "prioritized based on both customer value and risk?"
        ),
        interpretation=[
            (
                "Customers toward higher risk and higher revenue "
                "areas deserve greater investigation."
            ),
            (
                "Bubble size represents modeled revenue exposure."
            ),
            (
                "Revenue at Risk is not equivalent to forecast "
                "revenue loss."
            ),
        ],
        business_use=[
            "Retention prioritization.",
            "Commercial risk review.",
            "Executive account monitoring.",
        ],
        caveat=(
            "This metric represents modeled exposure based on "
            "Nexus360 project methodology. It is not an audited "
            "financial-loss forecast."
        ),
    )


# ============================================================
# CUSTOMER 360
# ============================================================


def _render_customer_360(
    customer_360: pd.DataFrame,
    rfm: pd.DataFrame,
    risk: pd.DataFrame,
) -> None:

    st.divider()

    st.subheader(
        "Customer 360 Drill-down"
    )

    st.caption(
        "Investigate a single customer across commercial value, "
        "subscriptions, support, cloud engagement, RFM behavior "
        "and risk."
    )

    if (
        customer_360.empty
        or "customer_id"
        not in customer_360.columns
    ):
        st.warning(
            "Customer 360 dataset is unavailable."
        )
        return

    customer_options = (
        customer_360[
            [
                "customer_id",
                "customer_name",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    customer_options[
        "label"
    ] = (
        customer_options[
            "customer_name"
        ].fillna(
            "Unknown Customer"
        ).astype(str)
        + " — "
        + customer_options[
            "customer_id"
        ].astype(str)
    )

    selected_label = st.selectbox(
        "Select customer",
        customer_options[
            "label"
        ].tolist(),
        index=0,
        help=(
            "Select an account to inspect its complete "
            "Customer 360 profile."
        ),
    )

    selected_id = (
        customer_options.loc[
            customer_options[
                "label"
            ] == selected_label,
            "customer_id",
        ]
        .iloc[0]
    )

    customer_row = customer_360[
        customer_360[
            "customer_id"
        ].astype(str)
        == str(selected_id)
    ]

    if customer_row.empty:
        st.warning(
            "Selected customer could not be loaded."
        )
        return

    customer = cast(
        dict[str, Any],
        customer_row
        .iloc[0]
        .to_dict(),
    )

    risk_record: dict[str, Any] | None = None

    if (
        not risk.empty
        and "customer_id"
        in risk.columns
    ):

        risk_row = risk[
            risk[
                "customer_id"
            ].astype(str)
            == str(selected_id)
        ]

        if not risk_row.empty:
            risk_record = cast(
                dict[str, Any],
                risk_row
                .iloc[0]
                .to_dict(),
            )

    rfm_record: dict[str, Any] | None = None

    if (
        not rfm.empty
        and "customer_id"
        in rfm.columns
    ):

        rfm_row = rfm[
            rfm[
                "customer_id"
            ].astype(str)
            == str(selected_id)
        ]

        if not rfm_row.empty:
            rfm_record = cast(
                dict[str, Any],
                rfm_row
                .iloc[0]
                .to_dict(),
            )

    st.markdown("---")

    render_customer_identity(
        customer
    )

    st.markdown("---")

    render_customer_commercial_value(
        customer
    )

    render_customer_subscription(
        customer
    )

    render_customer_support(
        customer
    )

    render_customer_cloud(
        customer
    )

    render_customer_risk(
        risk_record,
        rfm_record,
    )

    # --------------------------------------------------------
    # CUSTOMER-SPECIFIC EXPLANATION
    # --------------------------------------------------------

    lifetime_revenue = customer.get(
        "lifetime_revenue_usd",
        0,
    )

    risk_text = "No modeled risk record"

    if risk_record:
        risk_text = str(
            risk_record.get(
                "revenue_risk_band",
                "Unclassified",
            )
        )

    rfm_text = "No RFM segment"

    if rfm_record:
        rfm_text = str(
            rfm_record.get(
                "rfm_segment",
                "Unclassified",
            )
        )

    render_insight_panel(
        metric=(
            f"Customer lifetime revenue = "
            f"{format_currency(lifetime_revenue)}"
        ),
        insight=(
            f"The selected account is classified as "
            f"'{rfm_text}' by the RFM model and "
            f"'{risk_text}' by the commercial exposure model."
        ),
        potential_action=(
            "Use the detailed commercial, subscription, support "
            "and cloud signals above to investigate the drivers "
            "before deciding on an account action."
        ),
        warning=(
            risk_text.lower()
            in {
                "high",
                "critical",
                "very high",
            }
        ),
    )


# ============================================================
# MAIN PAGE
# ============================================================


def render() -> None:
    """
    Nexus360 Customer Intelligence page.
    """

    render_page_header(
        title="Customer Intelligence",
        subtitle=(
            "Customer value, behavioral segmentation, retention, "
            "subscription health and commercial-risk intelligence."
        ),
        eyebrow=(
            "NEXUS 360 • CUSTOMER & RETENTION INTELLIGENCE"
        ),
    )

    st.info(
        """
**What this page answers:**  
Who are our most valuable customers, how concentrated is customer
revenue, how are customers behaving over time, which subscriptions
show elevated renewal risk, and which accounts deserve deeper
commercial investigation?
        """
    )

    with st.spinner(
        "Loading customer intelligence..."
    ):
        data = load_customer_bundle()

    customer_360 = data[
        "customer_360"
    ].copy()

    rfm = data[
        "rfm"
    ].copy()

    pareto = data[
        "pareto"
    ].copy()

    value_tiers = data[
        "value_tiers"
    ].copy()

    cohort = data[
        "cohort"
    ].copy()

    subscriptions = data[
        "subscription_health"
    ].copy()

    renewal = data[
        "renewal_risk"
    ].copy()

    risk = data[
        "revenue_at_risk"
    ].copy()

    # ========================================================
    # PAGE NAVIGATION
    # ========================================================

    section = st.radio(
        "Customer Intelligence View",
        options=[
            "Portfolio",
            "Segmentation",
            "Retention & Subscriptions",
            "Risk Intelligence",
            "Customer 360",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ========================================================
    # PORTFOLIO
    # ========================================================

    if section == "Portfolio":

        _render_portfolio(
            customer_360,
            value_tiers,
            risk,
        )

        _render_pareto(
            pareto
        )

    # ========================================================
    # SEGMENTATION
    # ========================================================

    elif section == "Segmentation":

        _render_rfm(
            rfm
        )

        st.divider()

        st.subheader(
            "Customer Value Segmentation"
        )

        if not value_tiers.empty:

            preferred = [
                "customer_id",
                "customer_name",
                "customer_segment",
                "industry",
                "is_ai_customer",
                "lifetime_revenue",
                "lifetime_gross_profit",
                "gross_margin_pct",
                "products_purchased",
                "transaction_count",
                "value_quartile",
                "customer_value_tier",
            ]

            columns = [
                column
                for column in preferred
                if column
                in value_tiers.columns
            ]

            display = value_tiers.copy()

            if (
                "lifetime_revenue"
                in display.columns
            ):
                display[
                    "lifetime_revenue"
                ] = pd.to_numeric(
                    display[
                        "lifetime_revenue"
                    ],
                    errors="coerce",
                )

                display = (
                    display
                    .sort_values(
                        "lifetime_revenue",
                        ascending=False,
                    )
                )

            st.dataframe(
                display[
                    columns
                ],
                width="stretch",
                hide_index=True,
            )

            render_chart_guide(
                title="Customer Value Segmentation",
                definition=(
                    "Classifies customers according to "
                    "commercial value quartiles."
                ),
                business_question=(
                    "Which customers represent the strongest "
                    "commercial value?"
                ),
                interpretation=[
                    (
                        "Platinum customers represent the "
                        "highest value tier in the current "
                        "semantic model."
                    ),
                    (
                        "Value segmentation should be interpreted "
                        "alongside profitability, engagement and "
                        "risk."
                    ),
                ],
                business_use=[
                    "Key-account management.",
                    "Customer success prioritization.",
                    "Cross-sell targeting.",
                ],
            )

    # ========================================================
    # RETENTION
    # ========================================================

    elif section == "Retention & Subscriptions":

        _render_cohort(
            cohort
        )

        _render_subscription_health(
            subscriptions
        )

        _render_renewal_risk(
            renewal
        )

    # ========================================================
    # RISK
    # ========================================================

    elif section == "Risk Intelligence":

        _render_revenue_risk(
            risk
        )

    # ========================================================
    # CUSTOMER 360
    # ========================================================

    elif section == "Customer 360":

        _render_customer_360(
            customer_360,
            rfm,
            risk,
        )

    # ========================================================
    # METRIC DICTIONARY
    # ========================================================

    st.divider()

    render_metric_dictionary(
        [
            {
                "metric":
                    "RFM — Recency",
                "definition": (
                    "Number of days since the customer's "
                    "most recent purchase according to the "
                    "semantic-layer reference date."
                ),
                "formula": (
                    "Recency Days = Reference Date "
                    "- Last Purchase Date"
                ),
                "interpretation": (
                    "Lower values generally indicate more "
                    "recent purchase activity."
                ),
            },
            {
                "metric":
                    "RFM — Frequency",
                "definition": (
                    "Number of purchases or revenue-generating "
                    "transactions represented by the RFM model."
                ),
                "formula": (
                    "Frequency = Customer Purchase Count"
                ),
                "interpretation": (
                    "Higher frequency represents more repeated "
                    "commercial activity."
                ),
            },
            {
                "metric":
                    "RFM — Monetary Value",
                "definition": (
                    "Customer revenue represented in the RFM "
                    "model."
                ),
                "formula": (
                    "Monetary Value = SUM(Customer Revenue)"
                ),
                "interpretation": (
                    "Higher monetary value represents greater "
                    "historical commercial contribution."
                ),
            },
            {
                "metric":
                    "Cohort Retention %",
                "definition": (
                    "Percentage of customers from an acquisition "
                    "cohort that remain active at a given month "
                    "offset."
                ),
                "formula": (
                    "Retention % = "
                    "Active Cohort Customers / "
                    "Original Cohort Customers × 100"
                ),
                "interpretation": (
                    "Higher values indicate a larger retained "
                    "share of the original cohort."
                ),
            },
            {
                "metric":
                    "Active Subscription %",
                "definition": (
                    "Percentage of product subscriptions "
                    "currently classified as active."
                ),
                "formula": (
                    "Active Subscription % = "
                    "Active Subscriptions / "
                    "Total Subscriptions × 100"
                ),
                "interpretation": (
                    "Higher values indicate a larger active "
                    "subscription share."
                ),
            },
            {
                "metric":
                    "Auto-Renew %",
                "definition": (
                    "Percentage of subscriptions configured "
                    "for automatic renewal."
                ),
                "formula": (
                    "Auto-Renew % = "
                    "Auto-Renew Subscriptions / "
                    "Total Subscriptions × 100"
                ),
                "interpretation": (
                    "Auto-renew configuration is a subscription "
                    "signal and does not guarantee renewal."
                ),
            },
            {
                "metric":
                    "Renewal Risk Score",
                "definition": (
                    "Analytical score representing renewal-risk "
                    "signals in the Nexus360 semantic model."
                ),
                "formula": (
                    "Nexus360 semantic-layer renewal-risk logic"
                ),
                "interpretation": (
                    "Higher scores represent stronger modeled "
                    "renewal-risk signals."
                ),
            },
            {
                "metric":
                    "Revenue at Risk",
                "definition": (
                    "Modeled commercial exposure associated with "
                    "customers displaying elevated risk signals."
                ),
                "formula": (
                    "Customer Commercial Value × "
                    "Nexus360 Risk Exposure Methodology"
                ),
                "interpretation": (
                    "This is an analytical prioritization metric, "
                    "not guaranteed revenue loss."
                ),
            },
        ]
    )