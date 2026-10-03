from __future__ import annotations



from typing import Any



import pandas as pd

import streamlit as st



from src.ui.data_service import (

    load_executive_bundle,

    load_ml_bundle,

)





# ============================================================

# NEXUS360

# PREMIUM LIGHT LANDING PAGE

# ============================================================





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





def _format_currency(value: float) -> str:

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





def _navigate(page: str) -> None:

    st.session_state["nexus_requested_page"] = page

    st.rerun()





def _section_intro(
    eyebrow: str,
    title: str,
    description: str,
) -> None:
    """Render a safe, native Streamlit section introduction."""
    st.caption(eyebrow.upper())
    st.header(title)
    st.write(description)


def _render_module(
    title: str,
    description: str,
    capabilities: str,
    destination: str,
) -> None:
    """Render one landing-page module without raw HTML."""
    with st.container(border=True):
        st.subheader(title)
        st.write(description)
        st.caption(capabilities)
        if st.button(
            f"Explore {title} →",
            key=f"home_module_{destination.lower().replace(' ', '_').replace('&', 'and')}",
            use_container_width=True,
        ):
            _navigate(destination)


def _render_architecture_stage(
    stage: str,
    detail: str,
) -> None:
    """Render one architecture stage as a native Streamlit card."""
    with st.container(border=True):
        st.caption(stage)
        st.markdown(f"**{detail}**")


# ============================================================

# LIGHT LANDING THEME

# ============================================================





def _inject_home_css() -> None:
    """Apply the full-bleed Nexus360 dark landing-page visual system."""

    st.markdown(
        r"""
<style>
:root {
    --nx-bg: #050b14;
    --nx-bg-2: #071426;
    --nx-surface: #0b192c;
    --nx-surface-2: #10213a;
    --nx-blue: #3b82f6;
    --nx-indigo: #6366f1;
    --nx-cyan: #22d3ee;
    --nx-text: #f8fbff;
    --nx-body: #c7d5e8;
    --nx-muted: #8193ad;
    --nx-line: rgba(125, 164, 216, .18);
}

/* Full page canvas: remove the white gutters completely. */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background:
        radial-gradient(circle at 88% 8%, rgba(37,99,235,.18), transparent 25%),
        radial-gradient(circle at 12% 72%, rgba(79,70,229,.12), transparent 28%),
        linear-gradient(180deg, #050b14 0%, #071426 42%, #06101f 100%) !important;
    color: var(--nx-text) !important;
}

[data-testid="stHeader"] {
    background: rgba(5,11,20,.92) !important;
    border-bottom: 1px solid rgba(125,164,216,.12);
}

/* Full-width content. No large left/right empty margins. */
div[data-testid="stMainBlockContainer"] {
    max-width: none !important;
    width: 100% !important;
    padding: 0 0 5rem !important;
}

/* Keep non-hero content comfortably readable while retaining dark canvas. */
div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > div:not(:first-child) {
    width: min(1180px, calc(100% - 4rem));
    margin-left: auto;
    margin-right: auto;
}

/* ------------------------------------------------------------
   HERO — full bleed, viewport-fit, no side gaps
   ------------------------------------------------------------ */
.st-key-home_hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;
    width: 100% !important;
    min-height: calc(100vh - 3.75rem);
    margin: 0 !important;
    padding: clamp(2.2rem, 5vh, 4.2rem) clamp(2rem, 7vw, 8rem) !important;
    border: 0 !important;
    border-radius: 0 !important;
    background:
        radial-gradient(circle at 84% 18%, rgba(37,99,235,.23), transparent 28%),
        radial-gradient(circle at 78% 72%, rgba(34,211,238,.10), transparent 24%),
        linear-gradient(118deg, #050a13 0%, #071426 52%, #0a1c34 100%) !important;
    box-shadow: none !important;
}

/* Sculptural folded ribbon, kept on the far left. */
.st-key-home_hero::before {
    content: "";
    position: absolute;
    z-index: -2;
    left: -170px;
    top: -22vh;
    width: min(43vw, 650px);
    height: 145vh;
    border-radius: 46% 54% 58% 42% / 18% 28% 72% 82%;
    background:
        radial-gradient(ellipse at 70% 14%, rgba(147,197,253,.34), transparent 24%),
        linear-gradient(145deg, #2d4f98 0%, #101f47 20%, #3d65bc 39%, #101a3a 57%, #294e9c 76%, #071225 100%);
    transform: rotate(-7deg) skewY(-7deg);
    filter: drop-shadow(30px 22px 30px rgba(0,0,0,.46));
    opacity: .96;
}

.st-key-home_hero::after {
    content: "";
    position: absolute;
    z-index: -1;
    left: 7vw;
    top: -25vh;
    width: min(22vw, 340px);
    height: 150vh;
    border-radius: 58% 42% 48% 52% / 18% 34% 66% 82%;
    background: linear-gradient(155deg, rgba(124,162,244,.86) 0%, rgba(32,62,128,.9) 23%, rgba(5,13,31,.99) 44%, rgba(62,96,185,.92) 65%, rgba(9,19,43,.99) 85%);
    transform: rotate(8deg) skewY(8deg);
    filter: drop-shadow(24px 14px 26px rgba(0,0,0,.52));
    opacity: .9;
}

/* Compact copy so the complete hero fits in one viewport. */
.st-key-home_hero > div[data-testid="stVerticalBlock"] {
    position: relative;
    z-index: 3;
    width: min(820px, 62vw);
    margin-left: clamp(25rem, 34vw, 42rem);
    padding-top: clamp(.5rem, 3vh, 2rem);
    gap: .55rem !important;
}

.st-key-home_hero div[data-testid="stCaptionContainer"] {
    color: #8eddf4 !important;
    font-size: .73rem !important;
    font-weight: 800 !important;
    letter-spacing: .15em !important;
    text-transform: uppercase;
}

.st-key-home_hero h1 {
    margin: .2rem 0 .75rem !important;
    color: #f8fbff !important;
    font-size: clamp(3.1rem, 5.4vw, 5.9rem) !important;
    line-height: .94 !important;
    letter-spacing: -.065em !important;
    font-weight: 850 !important;
    text-wrap: balance;
}

.st-key-home_hero p {
    max-width: 760px;
    margin: .15rem 0 !important;
    color: #cbd9ea !important;
    font-size: clamp(.94rem, 1.15vw, 1.08rem) !important;
    line-height: 1.58 !important;
}

.st-key-home_hero .stButton > button {
    min-height: 3.05rem;
    border-radius: 13px;
    font-weight: 760;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}

.st-key-home_hero .stButton > button[kind="primary"] {
    color: #fff !important;
    border: 1px solid rgba(125,211,252,.42) !important;
    background: linear-gradient(105deg, #2563eb 0%, #4f46e5 58%, #0891b2 100%) !important;
    box-shadow: 0 14px 36px rgba(37,99,235,.25);
}

.st-key-home_hero .stButton > button:not([kind="primary"]) {
    color: #edf6ff !important;
    border: 1px solid rgba(148,163,184,.30) !important;
    background: rgba(255,255,255,.055) !important;
}

.st-key-home_hero .stButton > button:hover {
    transform: translateY(-2px);
    border-color: rgba(125,211,252,.65) !important;
}

/* ------------------------------------------------------------
   DARK CONTENT SYSTEM FOR THE REST OF THE PAGE
   ------------------------------------------------------------ */
div[data-testid="stAppViewContainer"] h1,
div[data-testid="stAppViewContainer"] h2,
div[data-testid="stAppViewContainer"] h3 {
    color: #f8fbff !important;
}

div[data-testid="stAppViewContainer"] h2 {
    font-size: clamp(2rem, 3.4vw, 3.1rem);
    line-height: 1.08;
    letter-spacing: -.045em;
    font-weight: 820;
}

div[data-testid="stAppViewContainer"] h3 {
    letter-spacing: -.025em;
    font-weight: 760;
}

div[data-testid="stAppViewContainer"] p,
div[data-testid="stMarkdownContainer"] li {
    color: #bdcce0 !important;
    line-height: 1.72;
}

div[data-testid="stCaptionContainer"] {
    color: #8193ad !important;
}

div[data-testid="stAppViewContainer"] hr {
    height: 1px;
    margin: 3.5rem auto;
    border: 0;
    background: linear-gradient(90deg, transparent, rgba(59,130,246,.30), rgba(34,211,238,.22), transparent);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(125,164,216,.18) !important;
    border-radius: 22px !important;
    background: linear-gradient(145deg, rgba(14,31,53,.96), rgba(8,21,38,.96)) !important;
    box-shadow: 0 16px 42px rgba(0,0,0,.18);
}

div[data-testid="stVerticalBlockBorderWrapper"]::before {
    content: "";
    position: absolute;
    inset: 0 8% auto;
    height: 2px;
    background: linear-gradient(90deg, transparent, #3b82f6, #6366f1, #22d3ee, transparent);
    opacity: .7;
}

div[data-testid="stMetric"] {
    position: relative;
    overflow: hidden;
    padding: 1.25rem 1.4rem !important;
    border: 1px solid rgba(125,164,216,.18) !important;
    border-radius: 20px !important;
    background: radial-gradient(circle at 96% 0%, rgba(79,70,229,.15), transparent 36%), #0b192c !important;
    box-shadow: 0 12px 32px rgba(0,0,0,.16) !important;
}

div[data-testid="stMetric"]::before {
    content: "";
    position: absolute;
    inset: 0 0 auto;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #6366f1, #22d3ee);
}

div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] p { color: #93a8c2 !important; }
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * { color: #f8fbff !important; font-weight: 840 !important; }

.stButton > button {
    min-height: 3.05rem;
    border: 1px solid rgba(125,164,216,.25) !important;
    border-radius: 13px;
    background: #0d1d32 !important;
    color: #eaf4ff !important;
    font-weight: 700;
}

.stButton > button[kind="primary"] {
    color: #fff !important;
    border-color: rgba(125,211,252,.35) !important;
    background: linear-gradient(105deg, #2563eb, #4f46e5 60%, #0891b2) !important;
}

div[data-testid="stAlert"],
div[data-testid="stExpander"],
div[data-testid="stDataFrame"],
div[data-testid="stPlotlyChart"] {
    border-radius: 18px !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071426 0%, #050b14 100%) !important;
    border-right: 1px solid rgba(96,165,250,.16);
}

/* Responsive: keep full bleed but move artwork behind the copy. */
@media (max-width: 1100px) {
    .st-key-home_hero > div[data-testid="stVerticalBlock"] {
        width: min(760px, 72vw);
        margin-left: 27vw;
    }
    .st-key-home_hero::before { left: -260px; opacity: .72; }
    .st-key-home_hero::after { left: -10px; opacity: .55; }
}

@media (max-width: 820px) {
    div[data-testid="stMainBlockContainer"] > div[data-testid="stVerticalBlock"] > div:not(:first-child) {
        width: calc(100% - 1.6rem);
    }
    .st-key-home_hero {
        min-height: calc(100svh - 3.5rem);
        padding: 2rem 1.25rem !important;
    }
    .st-key-home_hero::before { left: -360px; opacity: .46; }
    .st-key-home_hero::after { left: -160px; opacity: .30; }
    .st-key-home_hero > div[data-testid="stVerticalBlock"] {
        width: 100%;
        margin-left: 0;
        padding-top: 4vh;
    }
    .st-key-home_hero h1 { font-size: clamp(2.8rem, 13vw, 4.5rem) !important; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition-duration: .01ms !important; }
}
</style>
        """,
        unsafe_allow_html=True,
    )

def render() -> None:

    """

    Render the Nexus360 premium enterprise landing page.



    Design rules:

    - no st.columns()

    - no visible raw HTML

    - native Streamlit content

    - page-local light theme

    """



    _inject_home_css()



    # ========================================================

    # HERO

    # ========================================================

    with st.container(key="home_hero"):
        st.caption(
            "NEXUS360  •  ENTERPRISE DECISION INTELLIGENCE"
        )

        st.title(
            "Turn enterprise data into decisions."
        )

        st.write(
            "Nexus360 brings financial performance, customer intelligence, "
            "product analytics, cloud economics, predictive machine learning "
            "and grounded AI into one governed decision platform."
        )

        st.write(
            "Understand the business. Find the risk. Decide what to do next."
        )

        if st.button(
            "Open Executive Command Center  →",
            type="primary",
            width="stretch",
            key="home_command_center",
        ):
            _navigate(
                "Executive Command Center"
            )

        if st.button(
            "Ask Nexus AI",
            width="stretch",
            key="home_ai_copilot",
        ):
            _navigate(
                "AI Copilot"
            )

        st.caption(
            "PostgreSQL warehouse  •  Advanced analytics  •  "
            "Predictive ML  •  Grounded generative AI"
        )

    st.divider()

    # ========================================================

    # LOAD LIVE PLATFORM DATA

    # ========================================================



    executive: pd.DataFrame = pd.DataFrame()

    ml_summary: dict[str, Any] = {}



    executive_error: Exception | None = None

    ml_error: Exception | None = None



    try:

        executive_bundle = (

            load_executive_bundle()

        )



        executive = (

            executive_bundle[

                "executive"

            ].copy()

        )



    except Exception as exc:

        executive_error = exc



    try:

        ml_bundle = load_ml_bundle()



        ml_summary = ml_bundle[

            "summary"

        ]



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



    # ========================================================

    # LIVE INTELLIGENCE

    # ========================================================



    _section_intro(

        "Live platform intelligence",

        "Your business, at a glance.",

        (

            "A live executive view of commercial scale, "

            "customer reach and predictive exposure."

        ),

    )



    # Intentionally stacked.

    # No side-by-side metric columns.



    st.metric(

        "Enterprise Revenue",

        _format_currency(

            total_revenue

        ),

        help=(

            "Total revenue represented in the "

            "Nexus360 executive semantic layer."

        ),

    )



    st.metric(

        "Customers",

        _format_integer(

            total_customers

        ),

        help=(

            "Customer population represented by "

            "the executive analytics layer."

        ),

    )



    st.metric(

        "Gross Margin",

        f"{gross_margin:,.1f}%",

        help=(

            "Gross profit as a percentage "

            "of revenue."

        ),

    )



    st.metric(

        "Critical ML Risk",

        _format_integer(

            critical_customers

        ),

        help=(

            "Customers currently meeting the "

            "production churn-risk threshold."

        ),

    )



    if executive_error is not None:

        st.warning(

            "Executive KPIs are temporarily unavailable. "

            "The remaining platform can still be used."

        )



    if ml_error is not None:

        st.warning(

            "Predictive ML artifacts are temporarily "

            "unavailable. Run the scoring pipeline to "

            "refresh risk metrics."

        )



    if ml_summary:

        st.caption(

            f"{customers_scored:,} customers currently scored  •  "

            f"{_format_currency(expected_value_at_risk)} "

            f"probability-weighted contract value at risk"

        )



    st.divider()



    # ========================================================

    # INTELLIGENCE MODULES

    # ========================================================



    _section_intro(

        "The Nexus360 intelligence layer",

        "One platform. Every decision layer.",

        (

            "Move from executive performance to customer, "

            "product, cloud and market intelligence without "

            "breaking the analytical chain."

        ),

    )



    _render_module(

        "Executive Command Center",

        (

            "A single management view of enterprise scale, "

            "profitability, regional performance and material "

            "business exposure."

        ),

        (

            "Revenue  •  Profitability  •  Regions  •  "

            "Portfolio health"

        ),

        "Executive Command Center",

    )



    _render_module(

        "Revenue Intelligence",

        (

            "See how revenue changes over time and understand "

            "where commercial performance is being created."

        ),

        (

            "Trends  •  Growth  •  Mix  •  Concentration  •  "

            "Performance"

        ),

        "Revenue Intelligence",

    )



    _render_module(

        "Customer Intelligence",

        (

            "Connect customer value, behavior, retention, "

            "subscription health and commercial risk."

        ),

        (

            "Customer 360  •  RFM  •  Cohorts  •  Pareto  •  "

            "Renewal risk"

        ),

        "Customer Intelligence",

    )



    _render_module(

        "Product & AI Intelligence",

        (

            "Understand product economics, portfolio penetration "

            "and enterprise adoption of AI services."

        ),

        (

            "Product revenue  •  Penetration  •  AI adoption  •  "

            "Portfolio mix"

        ),

        "Product & AI Intelligence",

    )



    _render_module(

        "Cloud FinOps",

        (

            "Connect cloud consumption and operational usage "

            "to financial efficiency and business value."

        ),

        (

            "Usage  •  Cost  •  Unit economics  •  "

            "Efficiency  •  Optimization"

        ),

        "Cloud FinOps",

    )



    _render_module(

        "Market Intelligence",

        (

            "Combine geographic performance with external "

            "economic signals to identify commercial opportunity."

        ),

        (

            "Markets  •  Macroeconomics  •  FX exposure  •  "

            "Opportunity scoring"

        ),

        "Market Intelligence",

    )



    st.divider()



    # ========================================================

    # PREDICTIVE ML

    # ========================================================



    _section_intro(

        "Predictive intelligence",

        "See risk before it becomes an outcome.",

        (

            "Nexus360 converts historical customer evidence "

            "into current risk signals that management can "

            "prioritize and investigate."

        ),

    )



    st.markdown(

        """

The churn pipeline uses a **point-in-time historical training

design** to reduce leakage between model features and future

outcomes.



Historical model validation is separated from current customer

scoring so the production model can operate as a practical

**risk-ranking and prioritization system**.

        """

    )



    if ml_summary:

        model_name = str(

            ml_summary.get(

                "selected_model",

                "Unavailable",

            )

        ).replace(

            "_",

            " ",

        ).title()



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



        with st.container(

            border=True

        ):

            st.caption(

                "PRODUCTION MODEL"

            )



            st.subheader(

                model_name

            )



            st.metric(

                "Decision Threshold",

                f"{threshold:.2f}",

            )



            st.metric(

                "Flagged Rate",

                f"{predicted_rate:.1f}%",

            )



            st.caption(

                f"Current scoring population: "

                f"{customers_scored:,} customers"

            )



    else:

        with st.container(

            border=True

        ):

            st.subheader(

                "Predictive ML"

            )



            st.write(

                "Production model artifacts are "

                "not currently available."

            )



    st.info(

        "Model probabilities are analytical risk estimates, "

        "not guaranteed customer outcomes."

    )



    st.divider()



    # ========================================================

    # AI COPILOT

    # ========================================================



    _section_intro(

        "Nexus AI",

        "Ask the business. Get grounded answers.",

        (

            "A conversational intelligence layer over approved "

            "Nexus360 analytical context."

        ),

    )



    st.markdown(

        """

Nexus AI helps management **explain KPIs, interpret customer

risk, summarize business evidence and identify the next action**

without giving the model unrestricted database access.

        """

    )



    with st.container(

        border=True

    ):

        st.caption(

            "ASK NEXUS AI"

        )



        st.subheader(

            "Start with a business question."

        )



        st.write(

            "Which customers currently have the highest churn risk?"

        )



        st.write(

            "What is driving commercial exposure?"

        )



        st.write(

            "Which region generates the most revenue?"

        )



        st.write(

            "Where should management investigate next?"

        )



        if st.button(

            "Launch Nexus AI  →",

            type="primary",

            width="stretch",

            key="home_launch_ai",

        ):

            _navigate(

                "AI Copilot"

            )



    st.divider()



    # ========================================================

    # ARCHITECTURE

    # ========================================================



    _section_intro(

        "Platform architecture",

        "Built end to end.",

        (

            "One connected analytical path from source data "

            "to governed business intelligence."

        ),

    )



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



    for stage, detail in architecture_items:

        _render_architecture_stage(

            stage=stage,

            detail=detail,

        )



    st.divider()



    # ========================================================

    # FINAL CTA

    # ========================================================



    st.caption(

        "NEXUS360"

    )



    st.header(

        "From data to decision."

    )



    st.write(

        "Explore the complete enterprise intelligence "

        "platform from one connected workspace."

    )



    if st.button(

        "Enter Nexus360  →",

        type="primary",

        width="stretch",

        key="home_final_command_center",

    ):

        _navigate(

            "Executive Command Center"

        )



    st.divider()



    # ========================================================

    # FOOTER

    # ========================================================



    # Native Streamlit only.

    # No HTML footer and no columns.



        # ========================================================

    # PREMIUM FOOTER

    # ========================================================



    st.divider()



    st.caption(

        "NEXUS360  •  ENTERPRISE DECISION INTELLIGENCE"

    )



    st.header(

        "Built for better decisions."

    )



    st.write(

        "A connected intelligence platform bringing enterprise "

        "analytics, predictive risk and grounded AI into one "

        "decision experience."

    )



    if st.button(

        "Return to Executive Command Center  →",

        type="primary",

        width="stretch",

        key="home_footer_command_center",

    ):

        _navigate(

            "Executive Command Center"

        )



    st.markdown("")



    st.caption(

        "PLATFORM"

    )



    st.write(

        "Executive Analytics  •  Revenue Intelligence  •  "

        "Customer Intelligence  •  Product & AI  •  "

        "Cloud FinOps  •  Market Intelligence"

    )



    st.caption(

        "TECHNOLOGY"

    )



    st.write(

        "PostgreSQL  •  Advanced SQL  •  Python  •  "

        "Machine Learning  •  Gemini  •  Streamlit"

    )



    st.caption(

        "Nexus360 portfolio demonstration • "

        "Synthetic enterprise records + public-source data • "

        "Governed analytical context • "

        "AI outputs require human review"

    )



    st.caption(

        "© 2026 Nexus360  •  Enterprise Decision Intelligence"

    )