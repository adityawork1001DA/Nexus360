from __future__ import annotations

from html import escape

import streamlit as st


# ============================================================
# NEXUS 360
# Premium Enterprise Design System
# ============================================================

NEXUS_BLUE = "#3B82F6"
NEXUS_BLUE_BRIGHT = "#60A5FA"
NEXUS_CYAN = "#22D3EE"
NEXUS_VIOLET = "#8B5CF6"
NEXUS_GREEN = "#34D399"
NEXUS_AMBER = "#FBBF24"
NEXUS_RED = "#FB7185"

NEXUS_BG = "#050B14"
NEXUS_BG_ALT = "#071426"

NEXUS_SURFACE = "#0B1728"
NEXUS_SURFACE_ALT = "#10233A"
NEXUS_SURFACE_HOVER = "#15304D"

NEXUS_BORDER = "#1E3A5F"
NEXUS_BORDER_BRIGHT = "#2F5F91"

NEXUS_TEXT = "#F8FAFC"
NEXUS_TEXT_SOFT = "#D6E2F0"
NEXUS_MUTED = "#8FA7C0"


def apply_theme() -> None:
    """
    Apply the global Nexus360 premium enterprise theme.
    """

    css = f"""
<style>
/* ============================================================
   NEXUS 360 — GLOBAL DESIGN TOKENS
   ============================================================ */

:root {{
    --nx-blue: {NEXUS_BLUE};
    --nx-blue-bright: {NEXUS_BLUE_BRIGHT};
    --nx-cyan: {NEXUS_CYAN};
    --nx-violet: {NEXUS_VIOLET};

    --nx-green: {NEXUS_GREEN};
    --nx-amber: {NEXUS_AMBER};
    --nx-red: {NEXUS_RED};

    --nx-bg: {NEXUS_BG};
    --nx-bg-alt: {NEXUS_BG_ALT};

    --nx-surface: {NEXUS_SURFACE};
    --nx-surface-alt: {NEXUS_SURFACE_ALT};
    --nx-surface-hover: {NEXUS_SURFACE_HOVER};

    --nx-border: {NEXUS_BORDER};
    --nx-border-bright: {NEXUS_BORDER_BRIGHT};

    --nx-text: {NEXUS_TEXT};
    --nx-text-soft: {NEXUS_TEXT_SOFT};
    --nx-muted: {NEXUS_MUTED};

    --nx-radius-sm: 10px;
    --nx-radius-md: 14px;
    --nx-radius-lg: 18px;
    --nx-radius-xl: 24px;

    --nx-shadow-sm:
        0 8px 24px rgba(0, 0, 0, 0.18);

    --nx-shadow:
        0 18px 50px rgba(0, 0, 0, 0.24);

    --nx-shadow-blue:
        0 18px 45px rgba(37, 99, 235, 0.12);

    --nx-transition:
        180ms cubic-bezier(0.4, 0, 0.2, 1);
}}


/* ============================================================
   GLOBAL APPLICATION
   ============================================================ */

html {{
    scroll-behavior: smooth;
}}

body {{
    color: var(--nx-text);
}}

.stApp {{
    color: var(--nx-text);

    background:
        radial-gradient(
            circle at 4% 0%,
            rgba(37, 99, 235, 0.20),
            transparent 27%
        ),
        radial-gradient(
            circle at 96% 2%,
            rgba(34, 211, 238, 0.12),
            transparent 25%
        ),
        radial-gradient(
            circle at 68% 105%,
            rgba(139, 92, 246, 0.08),
            transparent 32%
        ),
        linear-gradient(
            145deg,
            #050B14 0%,
            #071426 48%,
            #050D19 100%
        );

    background-attachment: fixed;
}}

.block-container {{
    max-width: 1650px;

    padding-top: 1rem;
    padding-bottom: 5rem;

    padding-left: clamp(1rem, 2vw, 2rem);
    padding-right: clamp(1rem, 2vw, 2rem);
}}

::selection {{
    background: rgba(59, 130, 246, 0.50);
    color: #FFFFFF;
}}


/* ============================================================
   SCROLLBAR
   ============================================================ */

::-webkit-scrollbar {{
    width: 10px;
    height: 10px;
}}

::-webkit-scrollbar-track {{
    background: #050D18;
}}

::-webkit-scrollbar-thumb {{
    background:
        linear-gradient(
            180deg,
            #2A527E,
            #1D3B60
        );

    border-radius: 999px;

    border: 2px solid #050D18;
}}

::-webkit-scrollbar-thumb:hover {{
    background:
        linear-gradient(
            180deg,
            #3B82F6,
            #2563EB
        );
}}


/* ============================================================
   TYPOGRAPHY
   ============================================================ */

h1,
h2,
h3,
h4,
h5 {{
    color: var(--nx-text);

    letter-spacing: -0.025em;

    font-weight: 700;
}}

h1 {{
    letter-spacing: -0.04em;
}}

p,
li {{
    color: var(--nx-text-soft);

    line-height: 1.65;
}}

small {{
    color: var(--nx-muted);
}}

a {{
    color: #7DD3FC;

    text-decoration: none;

    transition:
        color var(--nx-transition);
}}

a:hover {{
    color: #BAE6FD;
}}

hr {{
    height: 1px;

    border: none;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(96, 165, 250, 0.35),
            rgba(34, 211, 238, 0.28),
            transparent
        );

    margin: 1.8rem 0;
}}


/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {{
    background:
        radial-gradient(
            circle at 15% 0%,
            rgba(37, 99, 235, 0.18),
            transparent 28%
        ),
        linear-gradient(
            180deg,
            #081525 0%,
            #06101D 100%
        );

    border-right:
        1px solid rgba(59, 130, 246, 0.22);

    box-shadow:
        8px 0 32px rgba(0, 0, 0, 0.12);
}}

section[data-testid="stSidebar"]
.block-container {{
    padding-top: 1.25rem;
}}

section[data-testid="stSidebar"]
[data-testid="stMarkdownContainer"] p {{
    color: #B9CBE0;
}}

section[data-testid="stSidebar"] hr {{
    background:
        linear-gradient(
            90deg,
            transparent,
            #23476F,
            transparent
        );
}}


/* ============================================================
   PAGE HEADER
   ============================================================ */

.nexus-header {{
    position: relative;

    isolation: isolate;

    overflow: hidden;

    padding:
        clamp(1.35rem, 2.2vw, 1.9rem)
        clamp(1.4rem, 2.5vw, 2rem);

    margin-bottom: 1.5rem;

    border:
        1px solid rgba(71, 123, 180, 0.52);

    border-radius:
        var(--nx-radius-xl);

    background:
        linear-gradient(
            115deg,
            rgba(16, 38, 70, 0.97) 0%,
            rgba(10, 27, 49, 0.97) 46%,
            rgba(8, 23, 41, 0.98) 100%
        );

    box-shadow:
        0 24px 65px rgba(0, 0, 0, 0.28),
        0 0 0 1px rgba(59, 130, 246, 0.025) inset,
        0 16px 42px rgba(37, 99, 235, 0.08);
}}

.nexus-header::before {{
    content: "";

    position: absolute;

    width: 520px;
    height: 520px;

    right: -170px;
    top: -340px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(34, 211, 238, 0.23) 0%,
            rgba(59, 130, 246, 0.11) 38%,
            transparent 70%
        );

    pointer-events: none;

    z-index: -1;
}}

.nexus-header::after {{
    content: "";

    position: absolute;

    left: 0;
    top: 0;
    bottom: 0;

    width: 4px;

    background:
        linear-gradient(
            180deg,
            #60A5FA 0%,
            #22D3EE 48%,
            #8B5CF6 100%
        );

    box-shadow:
        0 0 18px rgba(34, 211, 238, 0.55);

    z-index: 2;
}}

.nexus-eyebrow {{
    display: flex;

    align-items: center;

    gap: 0.5rem;

    margin-bottom: 0.55rem;

    color: #60A5FA;

    font-size: 0.73rem;

    font-weight: 800;

    letter-spacing: 0.16em;

    text-transform: uppercase;
}}

.nexus-eyebrow::before {{
    content: "";

    display: inline-block;

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: #22D3EE;

    box-shadow:
        0 0 10px rgba(34, 211, 238, 0.8);
}}

.nexus-title {{
    margin: 0;

    color: #FFFFFF;

    font-size:
        clamp(
            1.8rem,
            3vw,
            2.45rem
        );

    line-height: 1.13;

    font-weight: 800;

    letter-spacing: -0.045em;

    text-shadow:
        0 4px 20px rgba(0, 0, 0, 0.25);
}}

.nexus-subtitle {{
    max-width: 1050px;

    margin-top: 0.6rem;

    color: #A9BDD3;

    font-size: 0.97rem;

    line-height: 1.65;
}}


/* ============================================================
   KPI CARDS
   ============================================================ */

.nexus-kpi {{
    position: relative;

    overflow: hidden;

    min-height: 145px;

    padding: 1.1rem 1.2rem;

    border:
        1px solid rgba(49, 85, 126, 0.78);

    border-radius:
        var(--nx-radius-lg);

    background:
        linear-gradient(
            145deg,
            rgba(18, 42, 70, 0.94),
            rgba(11, 27, 46, 0.98)
        );

    box-shadow:
        var(--nx-shadow-sm);

    transition:
        transform var(--nx-transition),
        border-color var(--nx-transition),
        box-shadow var(--nx-transition);
}}

.nexus-kpi::before {{
    content: "";

    position: absolute;

    top: 0;
    left: 0;

    width: 100%;
    height: 2px;

    background:
        linear-gradient(
            90deg,
            #3B82F6,
            #22D3EE 52%,
            #8B5CF6,
            transparent
        );
}}

.nexus-kpi::after {{
    content: "";

    position: absolute;

    width: 130px;
    height: 130px;

    right: -70px;
    bottom: -75px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(59, 130, 246, 0.16),
            transparent 68%
        );

    pointer-events: none;
}}

.nexus-kpi:hover {{
    transform: translateY(-3px);

    border-color:
        rgba(96, 165, 250, 0.62);

    box-shadow:
        0 18px 42px rgba(0, 0, 0, 0.25),
        0 12px 32px rgba(37, 99, 235, 0.10);
}}

.nexus-kpi-label {{
    color: #91A9C3;

    font-size: 0.72rem;

    font-weight: 750;

    letter-spacing: 0.08em;

    text-transform: uppercase;
}}

.nexus-kpi-value {{
    margin-top: 0.42rem;

    color: #F8FAFC;

    font-size:
        clamp(
            1.55rem,
            2.5vw,
            1.95rem
        );

    line-height: 1.2;

    font-weight: 800;

    letter-spacing: -0.035em;
}}

.nexus-kpi-detail {{
    margin-top: 0.55rem;

    color: #8FA7C0;

    font-size: 0.78rem;

    line-height: 1.5;
}}

.nexus-positive {{
    color: #34D399 !important;
}}

.nexus-negative {{
    color: #FB7185 !important;
}}

.nexus-neutral {{
    color: #7DD3FC !important;
}}

.nexus-warning {{
    color: #FBBF24 !important;
}}


/* ============================================================
   STREAMLIT METRICS
   ============================================================ */

div[data-testid="stMetric"] {{
    position: relative;

    overflow: hidden;

    min-height: 125px;

    padding: 1.05rem;

    border:
        1px solid rgba(49, 85, 126, 0.72);

    border-radius:
        var(--nx-radius-lg);

    background:
        linear-gradient(
            145deg,
            rgba(17, 39, 66, 0.96),
            rgba(10, 25, 43, 0.98)
        );

    box-shadow:
        0 12px 32px rgba(0, 0, 0, 0.16);

    transition:
        transform var(--nx-transition),
        border-color var(--nx-transition),
        box-shadow var(--nx-transition);
}}

div[data-testid="stMetric"]::before {{
    content: "";

    position: absolute;

    left: 0;
    top: 0;

    width: 100%;
    height: 2px;

    background:
        linear-gradient(
            90deg,
            #3B82F6,
            #22D3EE,
            transparent 75%
        );
}}

div[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);

    border-color:
        rgba(96, 165, 250, 0.60);

    box-shadow:
        0 18px 40px rgba(0, 0, 0, 0.22);
}}

div[data-testid="stMetricLabel"] {{
    color: #8FA7C0;
}}

div[data-testid="stMetricValue"] {{
    color: #F8FAFC;

    letter-spacing: -0.035em;
}}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton > button,
.stDownloadButton > button {{
    min-height: 2.75rem;

    border:
        1px solid #31577F;

    border-radius:
        11px;

    background:
        linear-gradient(
            145deg,
            #163352,
            #10263F
        );

    color: #F8FAFC;

    font-weight: 650;

    box-shadow:
        0 8px 18px rgba(0, 0, 0, 0.15);

    transition:
        transform var(--nx-transition),
        border-color var(--nx-transition),
        background var(--nx-transition),
        box-shadow var(--nx-transition);
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
    transform: translateY(-2px);

    border-color: #60A5FA;

    background:
        linear-gradient(
            145deg,
            #1B426A,
            #143150
        );

    box-shadow:
        0 12px 28px rgba(0, 0, 0, 0.22),
        0 8px 20px rgba(37, 99, 235, 0.12);
}}

.stButton > button:active,
.stDownloadButton > button:active {{
    transform: translateY(0);
}}

.stButton > button[kind="primary"] {{
    border-color: #60A5FA;

    background:
        linear-gradient(
            120deg,
            #2563EB 0%,
            #3B82F6 48%,
            #0891B2 100%
        );

    box-shadow:
        0 10px 26px rgba(37, 99, 235, 0.28);
}}

.stButton > button[kind="primary"]:hover {{
    background:
        linear-gradient(
            120deg,
            #3B82F6,
            #2563EB 48%,
            #06B6D4
        );

    box-shadow:
        0 14px 34px rgba(37, 99, 235, 0.35);
}}

.stButton > button:disabled {{
    opacity: 0.45;

    transform: none;

    cursor: not-allowed;
}}


/* ============================================================
   INPUTS / SELECTS / TEXT AREAS
   ============================================================ */

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] {{
    background:
        rgba(10, 27, 48, 0.96);

    border-color:
        #29496D;

    border-radius:
        11px;

    transition:
        border-color var(--nx-transition),
        box-shadow var(--nx-transition),
        background var(--nx-transition);
}}

div[data-baseweb="input"]:focus-within > div,
div[data-baseweb="select"]:focus-within > div,
div[data-baseweb="textarea"]:focus-within {{
    border-color: #3B82F6;

    background:
        rgba(12, 32, 57, 0.98);

    box-shadow:
        0 0 0 3px rgba(59, 130, 246, 0.13);
}}

input,
textarea {{
    color: #F8FAFC !important;
}}

input::placeholder,
textarea::placeholder {{
    color: #647D99 !important;
}}


/* ============================================================
   TABS
   ============================================================ */

div[data-baseweb="tab-list"] {{
    gap: 0.4rem;

    border-bottom:
        1px solid rgba(49, 85, 126, 0.70);
}}

button[data-baseweb="tab"] {{
    color: #8FA7C0;

    font-weight: 680;

    padding-left: 1rem;
    padding-right: 1rem;

    border-radius:
        10px 10px 0 0;

    transition:
        color var(--nx-transition),
        background var(--nx-transition);
}}

button[data-baseweb="tab"]:hover {{
    color: #F8FAFC;

    background:
        rgba(59, 130, 246, 0.08);
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    color: #7DD3FC;

    background:
        linear-gradient(
            180deg,
            rgba(59, 130, 246, 0.14),
            rgba(34, 211, 238, 0.04)
        );
}}


/* ============================================================
   DATAFRAMES
   ============================================================ */

div[data-testid="stDataFrame"] {{
    overflow: hidden;

    border:
        1px solid rgba(49, 85, 126, 0.76);

    border-radius:
        var(--nx-radius-lg);

    background:
        rgba(8, 23, 41, 0.76);

    box-shadow:
        0 14px 36px rgba(0, 0, 0, 0.16);
}}


/* ============================================================
   PLOTLY CHARTS
   ============================================================ */

div[data-testid="stPlotlyChart"] {{
    overflow: hidden;

    padding: 0.35rem;

    border:
        1px solid rgba(49, 85, 126, 0.70);

    border-radius:
        var(--nx-radius-lg);

    background:
        linear-gradient(
            145deg,
            rgba(12, 31, 53, 0.82),
            rgba(7, 21, 38, 0.76)
        );

    box-shadow:
        0 14px 36px rgba(0, 0, 0, 0.14);

    transition:
        border-color var(--nx-transition),
        box-shadow var(--nx-transition);
}}

div[data-testid="stPlotlyChart"]:hover {{
    border-color:
        rgba(96, 165, 250, 0.46);

    box-shadow:
        0 18px 42px rgba(0, 0, 0, 0.18);
}}


/* ============================================================
   EXPANDERS
   ============================================================ */

div[data-testid="stExpander"] {{
    overflow: hidden;

    border:
        1px solid rgba(49, 85, 126, 0.72);

    border-radius:
        var(--nx-radius-md);

    background:
        linear-gradient(
            145deg,
            rgba(13, 31, 52, 0.88),
            rgba(8, 23, 41, 0.88)
        );

    box-shadow:
        0 10px 28px rgba(0, 0, 0, 0.12);
}}

div[data-testid="stExpander"] summary {{
    font-weight: 650;

    color: #DCE9F7;
}}


/* ============================================================
   ALERTS
   ============================================================ */

div[data-testid="stAlert"] {{
    border-radius:
        var(--nx-radius-md);

    border-width: 1px;

    box-shadow:
        0 10px 28px rgba(0, 0, 0, 0.12);
}}


/* ============================================================
   CODE
   ============================================================ */

code {{
    padding: 0.12rem 0.34rem;

    color: #BAE6FD;

    background:
        rgba(9, 26, 46, 0.96);

    border:
        1px solid rgba(49, 85, 126, 0.60);

    border-radius: 6px;
}}

pre {{
    border:
        1px solid var(--nx-border) !important;

    border-radius:
        var(--nx-radius-md) !important;

    box-shadow:
        0 12px 30px rgba(0, 0, 0, 0.16);
}}


/* ============================================================
   GENERIC NEXUS PANEL
   ============================================================ */

.nexus-panel {{
    position: relative;

    padding: 1.2rem 1.3rem;

    overflow: hidden;

    border:
        1px solid rgba(49, 85, 126, 0.72);

    border-radius:
        var(--nx-radius-lg);

    background:
        linear-gradient(
            145deg,
            rgba(16, 38, 64, 0.86),
            rgba(9, 25, 43, 0.92)
        );

    box-shadow:
        0 14px 34px rgba(0, 0, 0, 0.14);
}}


/* ============================================================
   STATUS BADGES
   ============================================================ */

.nexus-badge {{
    display: inline-flex;

    align-items: center;

    gap: 0.38rem;

    padding:
        0.3rem 0.68rem;

    border-radius: 999px;

    font-size: 0.72rem;

    font-weight: 750;

    letter-spacing: 0.025em;

    border:
        1px solid var(--nx-border);
}}

.nexus-badge-success {{
    color: #6EE7B7;

    background:
        rgba(16, 185, 129, 0.10);

    border-color:
        rgba(52, 211, 153, 0.30);
}}

.nexus-badge-warning {{
    color: #FCD34D;

    background:
        rgba(245, 158, 11, 0.10);

    border-color:
        rgba(251, 191, 36, 0.30);
}}

.nexus-badge-danger {{
    color: #FDA4AF;

    background:
        rgba(244, 63, 94, 0.10);

    border-color:
        rgba(251, 113, 133, 0.30);
}}

.nexus-badge-info {{
    color: #7DD3FC;

    background:
        rgba(37, 99, 235, 0.11);

    border-color:
        rgba(96, 165, 250, 0.30);
}}


/* ============================================================
   CAPTIONS
   ============================================================ */

div[data-testid="stCaptionContainer"] {{
    color: var(--nx-muted);
}}


/* ============================================================
   RESPONSIVE DESIGN
   ============================================================ */

@media (max-width: 900px) {{

    .block-container {{
        padding-top: 0.8rem;
        padding-left: 0.85rem;
        padding-right: 0.85rem;
    }}

    .nexus-header {{
        padding: 1.25rem;

        border-radius:
            var(--nx-radius-lg);
    }}

    .nexus-kpi {{
        min-height: 125px;
    }}

    .nexus-kpi-value {{
        white-space: normal;
    }}
}}


/* ============================================================
   REDUCED MOTION
   ============================================================ */

@media (prefers-reduced-motion: reduce) {{

    *,
    *::before,
    *::after {{
        scroll-behavior: auto !important;

        transition-duration:
            0.01ms !important;

        animation-duration:
            0.01ms !important;

        animation-iteration-count:
            1 !important;
    }}
}}


/* ============================================================
   HIDE DEFAULT STREAMLIT DECORATION
   ============================================================ */

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

</style>
"""

    st.markdown(
        css,
        unsafe_allow_html=True,
    )


def render_page_header(
    title: str,
    subtitle: str,
    eyebrow: str = "NEXUS 360",
) -> None:
    """
    Render the standard Nexus360 page header.

    IMPORTANT:
    The HTML is intentionally constructed without Markdown-style
    indentation. This prevents Streamlit from interpreting nested
    HTML as a Markdown code block.
    """

    safe_title = escape(
        str(title)
    )

    safe_subtitle = escape(
        str(subtitle)
    )

    safe_eyebrow = escape(
        str(eyebrow)
    )

    html = (
        '<div class="nexus-header">'
        f'<div class="nexus-eyebrow">{safe_eyebrow}</div>'
        f'<div class="nexus-title">{safe_title}</div>'
        f'<div class="nexus-subtitle">{safe_subtitle}</div>'
        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_status_badge(
    label: str,
    status: str = "info",
) -> None:
    """
    Render a Nexus360 status badge.

    Supported statuses:
    success, warning, danger, info.
    """

    normalized_status = (
        str(status)
        .strip()
        .lower()
    )

    allowed_statuses = {
        "success",
        "warning",
        "danger",
        "info",
    }

    if normalized_status not in allowed_statuses:
        normalized_status = "info"

    safe_label = escape(
        str(label)
    )

    html = (
        f'<span class="nexus-badge '
        f'nexus-badge-{normalized_status}">'
        f'{safe_label}'
        '</span>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_panel(
    content: str,
) -> None:
    """
    Render escaped text inside a Nexus360 panel.
    """

    safe_content = escape(
        str(content)
    )

    html = (
        '<div class="nexus-panel">'
        f'{safe_content}'
        '</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )