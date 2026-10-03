from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.ui.data_service import (
    load_executive_bundle,
    load_ml_bundle,
)


# ============================================================
# HELPERS
# ============================================================


def _first_numeric(
    dataframe: pd.DataFrame,
    candidates: list[str],
    default: float = 0.0,
) -> float:
    """
    Return the first valid numeric value found in the first row.
    """

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


def _format_currency(value: float) -> str:
    """
    Format large USD values for executive display.
    """

    absolute = abs(value)

    if absolute >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"

    if absolute >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"

    if absolute >= 1_000:
        return f"${value / 1_000:,.1f}K"

    return f"${value:,.0f}"


def _format_integer(value: float | int) -> str:
    return f"{int(value):,}"


def _inject_home_css() -> None:
    """
    Apply page-local light enterprise styling.

    The global application remains dark. This page creates a
    light workspace inside the main content area only.

    No dashboard content is rendered through raw HTML.
    """

    st.markdown(
        """
<style>
/* =========================================================
   NEXUS360 HOME - LIGHT ENTERPRISE WORKSPACE
========================================================= */

div[data-testid="stMainBlockContainer"] {
    max-width: 1600px;
}

/* Main landing canvas */
.nexus-home-shell {
    background:
        radial-gradient(
            circle at 90% 0%,
            rgba(37, 99, 235, 0.08),
            transparent 28%
        ),
        radial-gradient(
            circle at 10% 15%,
            rgba(6, 182, 212, 0.06),
            transparent 25%
        ),
        #F8FAFC;

    border: 1px solid #DCE5F0;
    border-radius: 24px;
    padding: 0.35rem 1.1rem 1.3rem 1.1rem;
    margin-bottom: 1rem;
    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.16);
}

/* Native Streamlit containers on home page */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #DCE5F0 !important;
    border-radius: 16px !important;
}

/* Home page headings */
.nexus-home-shell h1,
.nexus-home-shell h2,
.nexus-home-shell h3,
.nexus-home-shell p {
    color: #0F172A;
}

/* Native metrics */
.nexus-home-shell div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    box-shadow: none;
}

.nexus-home-shell div[data-testid="stMetricLabel"] {
    color: #64748B;
}

.nexus-home-shell div[data-testid="stMetricValue"] {
    color: #0F172A;
}

/* Buttons */
.nexus-home-shell .stButton > button {
    background: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    min-height: 2.7rem;
    font-weight: 650;
}

.nexus-home-shell .stButton > button:hover {
    border-color: #2563EB;
    color: #1D4ED8;
}

/* Primary buttons */
.nexus-home-shell .stButton > button[kind="primary"] {
    background: #2563EB;
    color: #FFFFFF;
    border-color: #2563EB;
}

.nexus-home-shell .stButton > button[kind="primary"]:hover {
    background: #1D4ED8;
    color: #FFFFFF;
}

/* Expander */
.nexus-home-shell details {
    background: #FFFFFF;
    border-color: #E2E8F0 !important;
}

/* Horizontal rule */
.nexus-home-shell hr {
    border-color: #E2E8F0;
}

/* Small text */
.nexus-home-shell small {
    color: #64748B;
}

/* Captions */
.nexus-home-shell div[data-testid="stCaptionContainer"] {
    color: #64748B;
}

/* Status/info boxes */
.nexus-home-shell div[data-testid="stAlert"] {
    border-radius: 14px;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_module(
    title: str,
    description: str,
    capabilities: str,
) -> None:
    """
    Render one native Streamlit platform module card.
    """

    with st.container(border=True):
        st.subheader(title)
        st.write(description)
        st.caption(capabilities)


def _render_architecture_stage(
    stage: str,
    detail: str,
) -> None:
    with st.container(border=True):
        st.caption(stage.upper())
        st.markdown(f"**{detail}**")


# ============================================================
# LANDING PAGE
# ============================================================


def render() -> None:
    """
    Render the Nexus360 enterprise landing page.
    """

    _inject_home_css()

    # Opening wrapper is intentionally tiny HTML used only as
    # a styling boundary. All visible content below uses native
        # Streamlit rendering.
    st.markdown(
        """
    <style>
    .stApp {
        background:
            radial-gradient(
                circle at 90% 0%,
                rgba(37, 99, 235, 0.05),
                transparent 26%
            ),
            #F8FAFC !important;
    }

    div[data-testid="stAppViewContainer"] {
        color: #0F172A;
    }

    div[data-testid="stAppViewContainer"] h1,
    div[data-testid="stAppViewContainer"] h2,
    div[data-testid="stAppViewContainer"] h3 {
        color: #0F172A !important;
    }

    div[data-testid="stAppViewContainer"] p {
        color: #475569;
    }

    div[data-testid="stAppViewContainer"] div[data-testid="stMetric"] {
        background: #FFFFFF;
        border-color: #E2E8F0;
    }

    div[data-testid="stAppViewContainer"] div[data-testid="stMetricValue"] {
        color: #0F172A;
    }
    </style>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # HERO
    # ========================================================

    hero_left, hero_right = st.columns(
        [1.7, 0.7],
        gap="large",
        vertical_alignment="center",
    )

    with hero_left:
        st.caption(
            "NEXUS360  /  ENTERPRISE DECISION INTELLIGENCE"
        )

        st.title(
            "Turn enterprise data into decisions."
        )

        st.markdown(
            """
Nexus360 unifies **financial performance, customer
intelligence, product analytics, cloud economics, market
opportunity, predictive machine learning and generative AI**
into one governed decision-intelligence platform.
            """
        )

        button_left, button_right, _ = st.columns(
            [1, 1, 1.4],
            gap="small",
        )

        with button_left:
            if st.button(
                "Open Command Center",
                type="primary",
                width="stretch",
                key="home_command_center",
            ):
                st.session_state["nexus_requested_page"] = (
                    "Executive Command Center"
                )
                st.rerun()

        with button_right:
            if st.button(
                "Ask Nexus AI",
                width="stretch",
                key="home_ai_copilot",
            ):
                st.session_state["nexus_requested_page"] = (
                    "AI Copilot"
                )
                st.rerun()

    with hero_right:
        with st.container(border=True):
            st.caption("PLATFORM STATUS")
            st.subheader("Operational")
            st.write(
                "Warehouse, analytics, predictive ML and "
                "grounded AI are connected."
            )

            st.divider()

            st.caption("DECISION LAYERS")
            st.markdown(
                """
**6** analytical domains  
**1** predictive ML layer  
**1** grounded AI copilot
                """
            )

    st.divider()

    # ========================================================
    # LIVE PLATFORM INTELLIGENCE
    # ========================================================

    st.caption("LIVE PLATFORM INTELLIGENCE")
    st.header("Enterprise intelligence at a glance")

    executive: pd.DataFrame = pd.DataFrame()
    ml_summary: dict[str, Any] = {}

    executive_error: Exception | None = None
    ml_error: Exception | None = None

    try:
        executive_bundle = load_executive_bundle()
        executive = executive_bundle["executive"].copy()
    except Exception as exc:
        executive_error = exc

    try:
        ml_bundle = load_ml_bundle()
        ml_summary = ml_bundle["summary"]
    except Exception as exc:
        ml_error = exc

    total_revenue = _first_numeric(
        executive,
        [
            "total_revenue_usd",
            "net_revenue_usd",
            "revenue_usd",
        ],
    )

    total_customers = _first_numeric(
        executive,
        [
            "total_customers",
            "customer_count",
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

    customers_scored = int(
        ml_summary.get(
            "customers_scored",
            0,
        )
    )

    critical_customers = int(
        ml_summary.get(
            "risk_distribution",
            {},
        ).get(
            "Critical",
            0,
        )
    )

    expected_value_at_risk = float(
        ml_summary.get(
            "expected_contract_value_at_risk_usd",
            0.0,
        )
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            "Enterprise Revenue",
            _format_currency(total_revenue),
            help=(
                "Total revenue represented in the Nexus360 "
                "executive semantic layer."
            ),
        )

    with kpi2:
        st.metric(
            "Customers",
            _format_integer(total_customers),
            help=(
                "Customer population represented by the "
                "executive analytics layer."
            ),
        )

    with kpi3:
        st.metric(
            "Gross Margin",
            f"{gross_margin:,.1f}%",
            help=(
                "Gross profit as a percentage of revenue."
            ),
        )

    with kpi4:
        st.metric(
            "Critical ML Risk",
            _format_integer(critical_customers),
            help=(
                "Customers whose current modeled churn "
                "probability meets the production decision "
                "threshold."
            ),
        )

    if executive_error is not None:
        st.warning(
            "Executive KPIs are temporarily unavailable. "
            "The remaining platform modules can still be used."
        )

    if ml_error is not None:
        st.warning(
            "Predictive ML artifacts are temporarily unavailable. "
            "Run the ML scoring pipeline to refresh risk metrics."
        )

    if ml_summary:
        st.caption(
            f"Predictive layer currently scores "
            f"{customers_scored:,} customers with "
            f"{_format_currency(expected_value_at_risk)} "
            f"in probability-weighted expected contract value "
            f"at risk."
        )

    st.divider()

    # ========================================================
    # ANALYTICAL MODULES
    # ========================================================

    st.caption("THE NEXUS360 INTELLIGENCE LAYER")
    st.header("One platform. Multiple decision domains.")

    st.write(
        "Each analytical module answers a different class of "
        "enterprise decision while sharing a common governed "
        "warehouse and semantic layer."
    )

    row1 = st.columns(3, gap="medium")

    with row1[0]:
        _render_module(
            "Executive Command Center",
            (
                "A consolidated view of enterprise scale, "
                "profitability, commercial performance and "
                "material business exposure."
            ),
            (
                "Revenue • Profitability • Regions • "
                "Portfolio health"
            ),
        )

    with row1[1]:
        _render_module(
            "Revenue Intelligence",
            (
                "Explains how revenue changes over time and "
                "where financial performance is being created."
            ),
            (
                "Trends • Growth • Mix • Concentration • "
                "Performance"
            ),
        )

    with row1[2]:
        _render_module(
            "Customer Intelligence",
            (
                "Combines customer value, behavior, retention, "
                "subscription health and commercial risk."
            ),
            (
                "Customer 360 • RFM • Cohorts • Pareto • "
                "Renewal risk"
            ),
        )

    row2 = st.columns(3, gap="medium")

    with row2[0]:
        _render_module(
            "Product & AI Intelligence",
            (
                "Measures product economics, portfolio "
                "penetration and enterprise adoption of AI "
                "services."
            ),
            (
                "Product revenue • Penetration • AI adoption • "
                "Portfolio mix"
            ),
        )

    with row2[1]:
        _render_module(
            "Cloud FinOps",
            (
                "Connects cloud consumption and operational "
                "usage to financial efficiency and business "
                "value."
            ),
            (
                "Usage • Cost • Unit economics • Efficiency • "
                "Optimization"
            ),
        )

    with row2[2]:
        _render_module(
            "Market Intelligence",
            (
                "Combines geographic performance with external "
                "economic signals to identify commercial "
                "opportunity."
            ),
            (
                "Markets • Macroeconomics • FX exposure • "
                "Opportunity scoring"
            ),
        )

    st.divider()

    # ========================================================
    # PREDICTIVE ML
    # ========================================================

    st.caption("PREDICTIVE INTELLIGENCE")
    st.header("From historical evidence to current risk.")

    predictive_left, predictive_right = st.columns(
        [1.35, 1],
        gap="large",
    )

    with predictive_left:
        st.markdown(
            """
Nexus360's churn pipeline uses a **point-in-time historical
training design** to reduce leakage between model features and
future outcomes.

The production workflow separates historical model validation
from current customer scoring, allowing management to use the
model primarily as a **risk-ranking and prioritization system**.
            """
        )

        st.info(
            "Model probabilities are analytical risk estimates, "
            "not guaranteed customer outcomes."
        )

    with predictive_right:
        if ml_summary:
            model_name = str(
                ml_summary.get(
                    "selected_model",
                    "Unavailable",
                )
            ).replace("_", " ").title()

            threshold = float(
                ml_summary.get(
                    "decision_threshold",
                    0.0,
                )
            )

            predicted_rate = float(
                ml_summary.get(
                    "predicted_churn_rate_pct",
                    0.0,
                )
            )

            with st.container(border=True):
                st.caption("PRODUCTION MODEL")
                st.subheader(model_name)

                a, b = st.columns(2)

                with a:
                    st.metric(
                        "Decision Threshold",
                        f"{threshold:.2f}",
                    )

                with b:
                    st.metric(
                        "Flagged Rate",
                        f"{predicted_rate:.1f}%",
                    )

                st.caption(
                    f"Current scoring population: "
                    f"{customers_scored:,} customers"
                )

        else:
            with st.container(border=True):
                st.subheader("Predictive ML")
                st.write(
                    "Production artifacts are not currently "
                    "available."
                )

    st.divider()

    # ========================================================
    # AI COPILOT
    # ========================================================

    st.caption("NEXUS AI")
    st.header("Ask the analytical platform.")

    ai_left, ai_right = st.columns(
        [1.2, 1],
        gap="large",
    )

    with ai_left:
        st.markdown(
            """
The Nexus AI Copilot provides a conversational layer over
approved Nexus360 analytical context.

It is designed to:

- explain KPIs and analytical terminology,
- interpret modeled customer risk,
- summarize available business evidence,
- recommend management actions from supplied context,
- refuse credential and database-modification requests, and
- state when the available context cannot support an answer.
            """
        )

    with ai_right:
        with st.container(border=True):
            st.caption("EXAMPLE MANAGEMENT QUESTIONS")

            st.markdown(
                """
**Which customers currently have the highest churn risk?**

**What is driving commercial exposure?**

**How should management interpret the model's precision and recall?**

**Which analytical area should I investigate next?**
                """
            )

            if st.button(
                "Launch AI Copilot",
                type="primary",
                width="stretch",
                key="home_launch_ai",
            ):
                st.session_state["nexus_requested_page"] = (
                    "AI Copilot"
                )
                st.rerun()

    st.divider()

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    st.caption("PLATFORM ARCHITECTURE")
    st.header("Built as an end-to-end analytical system.")

    architecture = st.columns(6, gap="small")

    architecture_items = [
        (
            "01 / DATA",
            "Enterprise + Public Sources",
        ),
        (
            "02 / WAREHOUSE",
            "PostgreSQL",
        ),
        (
            "03 / SEMANTIC",
            "Advanced SQL",
        ),
        (
            "04 / ANALYTICS",
            "Python + Pandas",
        ),
        (
            "05 / PREDICTIVE",
            "Machine Learning",
        ),
        (
            "06 / EXPERIENCE",
            "Gemini + Streamlit",
        ),
    ]

    for column, item in zip(
        architecture,
        architecture_items,
    ):
        with column:
            _render_architecture_stage(
                stage=item[0],
                detail=item[1],
            )

    st.divider()

    # ========================================================
    # FOOTER
    # ========================================================

    footer_left, footer_right = st.columns(
        [1.5, 1],
        vertical_alignment="center",
    )

    with footer_left:
        st.markdown(
            "**Nexus360 Enterprise Analytics Platform**"
        )
        st.caption(
            "Decision Intelligence • Predictive Analytics • "
            "Grounded Generative AI"
        )

    with footer_right:
        st.caption(
            "Portfolio demonstration using synthetic enterprise "
            "records and public-source analytical data."
        )