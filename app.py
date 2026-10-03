from __future__ import annotations

import streamlit as st

from src.ui.data_service import (
    clear_dashboard_cache,
)
from src.ui.pages.ai import (
    render as render_ai,
)
from src.ui.pages.cloud import (
    render as render_cloud,
)
from src.ui.pages.customer import (
    render as render_customer,
)
from src.ui.pages.executive import (
    render as render_executive,
)
from src.ui.pages.home import (
    render as render_home,
)
from src.ui.pages.market import (
    render as render_market,
)
from src.ui.pages.ml import (
    render as render_ml,
)
from src.ui.pages.product import (
    render as render_product,
)
from src.ui.pages.revenue import (
    render as render_revenue,
)

from src.ui.pages.admin import (
    render as render_admin,
)
from src.ui.theme import apply_theme


# ============================================================
# STREAMLIT CONFIG
# ============================================================


st.set_page_config(
    page_title="Nexus360",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


apply_theme()


# ============================================================
# NAVIGATION
# ============================================================


PAGES = [
    "Nexus360 Overview",
    "Executive Command Center",
    "Revenue Intelligence",
    "Customer Intelligence",
    "Product & AI Intelligence",
    "Cloud FinOps",
    "Market Intelligence",
    "Predictive ML",
    "AI Copilot",
    "Admin Control Center",
]


def _navigation_index() -> int:
    requested = st.session_state.pop(
        "nexus_requested_page",
        None,
    )

    if requested in PAGES:
        return PAGES.index(requested)

    return 0


# ============================================================
# SIDEBAR
# ============================================================


def render_sidebar() -> str:
    """
    Render Nexus360 application navigation.
    """

    with st.sidebar:

        st.markdown(
            """
# ◆ NEXUS 360

**Enterprise Decision Intelligence**
            """
        )

        st.caption(
            "Analytics • Predictive ML • Generative AI"
        )

        st.divider()

        # ----------------------------------------------------
        # HOME
        # ----------------------------------------------------

        st.caption("PLATFORM")

        page = st.radio(
            "Navigation",
            options=PAGES,
            index=_navigation_index(),
            label_visibility="collapsed",
        )

        st.divider()

        # ----------------------------------------------------
        # DATA CONTROL
        # ----------------------------------------------------

        st.caption("DATA CONTROL")

        if st.button(
            "↻ Refresh Analytics",
            width="stretch",
        ):
            clear_dashboard_cache()

            st.success(
                "Analytics and model artifact cache cleared."
            )

            st.rerun()

        st.divider()

        # ----------------------------------------------------
        # PLATFORM STATUS
        # ----------------------------------------------------

        st.caption("PLATFORM CAPABILITIES")

        st.markdown(
            """
✓ Enterprise Warehouse  
✓ External Data Integration  
✓ Semantic SQL Layer  
✓ Executive Intelligence  
✓ Revenue Intelligence  
✓ Customer Intelligence  
✓ Product & AI Intelligence  
✓ Cloud FinOps  
✓ Market Intelligence  
✓ Predictive Churn ML  
✓ Gemini AI Copilot
            """
        )

        st.divider()

        # ----------------------------------------------------
        # STACK
        # ----------------------------------------------------

        st.caption("ANALYTICS STACK")

        st.markdown(
            """
`PostgreSQL`  
`Advanced SQL`  
`Python Analytics`  
`Pandas / NumPy`  
`Machine Learning`  
`Gemini AI`  
`Excel BI`  
`Tableau`  
`Streamlit`
            """
        )

        st.divider()

        st.caption(
            "Portfolio demonstration using synthetic enterprise "
            "records and public-source analytical data."
        )

    return page


# ============================================================
# APPLICATION ROUTER
# ============================================================


def main() -> None:
    """
    Route the selected Nexus360 application page.
    """

    page = render_sidebar()

    if page == "Nexus360 Overview":
        render_home()

    elif page == "Executive Command Center":
        render_executive()

    elif page == "Revenue Intelligence":
        render_revenue()

    elif page == "Customer Intelligence":
        render_customer()

    elif page == "Product & AI Intelligence":
        render_product()

    elif page == "Cloud FinOps":
        render_cloud()

    elif page == "Market Intelligence":
        render_market()

    elif page == "Predictive ML":
        render_ml()

    elif page == "AI Copilot":
        render_ai()

    elif page == "Admin Control Center":
        render_admin()

    else:
        render_home()


if __name__ == "__main__":
    main()