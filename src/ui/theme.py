from __future__ import annotations

from textwrap import dedent

import streamlit as st


NEXUS_BLUE = "#2563EB"
NEXUS_CYAN = "#06B6D4"
NEXUS_GREEN = "#10B981"
NEXUS_AMBER = "#F59E0B"
NEXUS_RED = "#EF4444"

NEXUS_BG = "#07111F"
NEXUS_SURFACE = "#0F1B2D"
NEXUS_SURFACE_ALT = "#132238"
NEXUS_BORDER = "#233650"

NEXUS_TEXT = "#F8FAFC"
NEXUS_MUTED = "#94A3B8"


def apply_theme() -> None:
    """
    Apply the global Nexus360 enterprise UI theme.
    """

    css = """
    <style>

    /* =========================================================
       APPLICATION
    ========================================================= */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 0%,
                rgba(37, 99, 235, 0.12),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(6, 182, 212, 0.08),
                transparent 24%
            ),
            #07111F;

        color: #F8FAFC;
    }

    .block-container {
        max-width: 1600px;
        padding-top: 1.4rem;
        padding-bottom: 4rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }


    /* =========================================================
       SIDEBAR
    ========================================================= */

    section[data-testid="stSidebar"] {
        background: #0A1525;
        border-right: 1px solid #233650;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }


    /* =========================================================
       TYPOGRAPHY
    ========================================================= */

    h1,
    h2,
    h3 {
        color: #F8FAFC;
        letter-spacing: -0.02em;
    }

    p {
        color: #CBD5E1;
    }


    /* =========================================================
       NEXUS HEADER
    ========================================================= */

    .nexus-header {
        padding: 1.2rem 1.4rem;

        border: 1px solid #233650;

        border-radius: 18px;

        background:
            linear-gradient(
                135deg,
                rgba(37, 99, 235, 0.16),
                rgba(15, 27, 45, 0.96)
            );

        margin-bottom: 1.2rem;

        box-shadow:
            0 12px 35px
            rgba(0, 0, 0, 0.14);
    }

    .nexus-eyebrow {
        color: #60A5FA;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .nexus-title {
        color: #F8FAFC;
        font-size: 2rem;
        line-height: 1.2;
        font-weight: 750;
        margin: 0;
    }

    .nexus-subtitle {
        color: #94A3B8;
        margin-top: 0.45rem;
        margin-bottom: 0;
        line-height: 1.6;
    }


    /* =========================================================
       KPI CARDS
    ========================================================= */

    .nexus-kpi {
        min-height: 142px;

        padding: 1rem 1.1rem;

        border-radius: 16px;

        border: 1px solid #233650;

        background:
            linear-gradient(
                180deg,
                rgba(19, 34, 56, 0.96),
                rgba(15, 27, 45, 0.96)
            );

        box-shadow:
            0 10px 30px
            rgba(0, 0, 0, 0.15);

        overflow: hidden;
    }

    .nexus-kpi-label {
        color: #94A3B8;
        font-size: 0.78rem;
        font-weight: 650;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.4rem;
    }

    .nexus-kpi-value {
        color: #F8FAFC;
        font-size: 1.7rem;
        line-height: 1.25;
        font-weight: 750;
        margin-top: 0.35rem;
        white-space: nowrap;
    }

    .nexus-kpi-detail {
        font-size: 0.78rem;
        line-height: 1.45;
        margin-top: 0.55rem;
    }

    .nexus-positive {
        color: #34D399;
    }

    .nexus-negative {
        color: #F87171;
    }

    .nexus-neutral {
        color: #93C5FD;
    }


    /* =========================================================
       DATAFRAMES
    ========================================================= */

    div[data-testid="stDataFrame"] {
        border: 1px solid #233650;
        border-radius: 14px;
        overflow: hidden;
    }


    /* =========================================================
       TABS
    ========================================================= */

    button[data-baseweb="tab"] {
        font-weight: 650;
    }


    /* =========================================================
       BUTTONS
    ========================================================= */

    .stButton > button {
        border-radius: 10px;
        border: 1px solid #315078;
    }


    /* =========================================================
       STREAMLIT METRICS
    ========================================================= */

    div[data-testid="stMetric"] {
        background: #0F1B2D;
        border: 1px solid #233650;
        padding: 1rem;
        border-radius: 14px;
    }


    /* =========================================================
       PLOTLY
    ========================================================= */

    div[data-testid="stPlotlyChart"] {
        border: 1px solid rgba(35, 54, 80, 0.65);
        border-radius: 16px;
        padding: 0.25rem;
        background: rgba(15, 27, 45, 0.35);
    }


    /* =========================================================
       HIDE DEFAULT STREAMLIT DECORATION
    ========================================================= */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """

    st.markdown(
        dedent(css),
        unsafe_allow_html=True,
    )


def render_page_header(
    title: str,
    subtitle: str,
    eyebrow: str = "NEXUS 360",
) -> None:
    """
    Render the standard Nexus360 page header.

    dedent() is important here because Markdown interprets
    indented HTML as a code block.
    """

    html = f"""
    <div class="nexus-header">
        <div class="nexus-eyebrow">{eyebrow}</div>
        <div class="nexus-title">{title}</div>
        <div class="nexus-subtitle">{subtitle}</div>
    </div>
    """

    st.markdown(
        dedent(html).strip(),
        unsafe_allow_html=True,
    )