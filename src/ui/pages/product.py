from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.data_loader import AnalyticsDataLoader
from src.ui.components.product import (
    render_ai_adoption_by_segment,
    render_ai_customer_value_comparison,
    render_ai_economics,
    render_ai_industry_heatmap,
    render_ai_opportunity_table,
    render_penetration_chart,
    render_portfolio_kpis,
    render_product_table,
    render_revenue_leaderboard,
    render_revenue_penetration_matrix,
)


@st.cache_data(ttl=300, show_spinner=False)
def load_product_intelligence_data() -> dict[str, pd.DataFrame]:
    loader = AnalyticsDataLoader()

    return {
        "ranking": loader.load_view(
            "v_product_revenue_rank"
        ),
        "penetration": loader.load_view(
            "v_product_penetration"
        ),
        "ai": loader.load_view(
            "v_ai_adoption"
        ),
    }


def _apply_filters(
    ranking: pd.DataFrame,
    penetration: pd.DataFrame,
    ai: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    st.sidebar.markdown("### Product Intelligence Filters")

    families = sorted(
        penetration["product_family"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_families = st.sidebar.multiselect(
        "Product Family",
        families,
        default=families,
        key="product_family_filter",
    )

    service_categories = sorted(
        penetration["service_category"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_categories = st.sidebar.multiselect(
        "Service Category",
        service_categories,
        default=service_categories,
        key="product_service_category_filter",
    )

    ai_service_filter = st.sidebar.selectbox(
        "AI Service",
        [
            "All Products",
            "AI Services",
            "Non-AI Services",
        ],
        key="product_ai_service_filter",
    )

    segments = sorted(
        ai["customer_segment"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_segments = st.sidebar.multiselect(
        "Customer Segment",
        segments,
        default=segments,
        key="product_customer_segment_filter",
    )

    industries = sorted(
        ai["industry"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_industries = st.sidebar.multiselect(
        "Industry",
        industries,
        default=industries,
        key="product_industry_filter",
    )

    filtered_penetration = penetration[
        penetration["product_family"].isin(
            selected_families
        )
        & penetration["service_category"].isin(
            selected_categories
        )
    ].copy()

    if ai_service_filter == "AI Services":
        filtered_penetration = filtered_penetration[
            filtered_penetration["is_ai_service"]
        ]

    elif ai_service_filter == "Non-AI Services":
        filtered_penetration = filtered_penetration[
            ~filtered_penetration["is_ai_service"]
        ]

    selected_products = set(
        filtered_penetration["product_code"]
    )

    filtered_ranking = ranking[
        ranking["product_code"].isin(
            selected_products
        )
    ].copy()

    filtered_ai = ai[
        ai["customer_segment"].isin(
            selected_segments
        )
        & ai["industry"].isin(
            selected_industries
        )
    ].copy()

    return (
        filtered_ranking,
        filtered_penetration,
        filtered_ai,
    )


def render() -> None:

    st.title("Product & AI Intelligence")

    st.caption(
        "Enterprise product portfolio analytics, customer penetration, "
        "AI adoption and monetisation intelligence."
    )

    st.info(
        """
This dashboard answers four executive questions:

**1. Which products drive the business?**  
Revenue ranking identifies the largest commercial contributors.

**2. How deeply are products adopted?**  
Customer penetration shows how much of the existing customer base uses each product.

**3. Where is AI adoption strongest?**  
Industry and customer-segment analytics reveal adoption patterns.

**4. Is AI adoption commercially valuable?**  
Revenue and gross-profit metrics evaluate AI customer economics.

Use the sidebar filters to explore specific product families, service categories,
customer segments and industries.
"""
    )

    try:
        bundle = load_product_intelligence_data()

    except Exception as exc:
        st.error(
            "Unable to load Product Intelligence data."
        )
        st.exception(exc)
        return

    ranking = bundle["ranking"]
    penetration = bundle["penetration"]
    ai = bundle["ai"]

    if ranking.empty:
        st.warning(
            "Product revenue ranking contains no data."
        )
        return

    if penetration.empty:
        st.warning(
            "Product penetration contains no data."
        )
        return

    if ai.empty:
        st.warning(
            "AI adoption contains no data."
        )
        return

    (
        ranking,
        penetration,
        ai,
    ) = _apply_filters(
        ranking,
        penetration,
        ai,
    )

    if (
        ranking.empty
        or penetration.empty
        or ai.empty
    ):
        st.warning(
            "No records match the selected filters."
        )
        return

    st.markdown("---")

    render_portfolio_kpis(
        ranking,
        penetration,
        ai,
    )

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Portfolio Performance",
            "Product Adoption",
            "AI Intelligence",
            "Opportunity Explorer",
        ]
    )

    with tab1:

        st.markdown(
            """
### Portfolio Performance

This section evaluates the commercial contribution of each product.

Use it to understand whether revenue is diversified across the portfolio
or concentrated in a small number of services.
"""
        )

        render_revenue_leaderboard(
            ranking
        )

        st.markdown("---")

        render_product_table(
            penetration
        )

    with tab2:

        st.markdown(
            """
### Product Adoption

Revenue and adoption measure different dimensions of product success.

A product can have:

- **High revenue + high penetration** → established portfolio leader.
- **High revenue + lower penetration** → potentially attractive expansion opportunity.
- **Lower revenue + high penetration** → widely adopted but potentially under-monetised.
- **Lower revenue + lower penetration** → product requiring deeper strategic review.

The matrix below makes these patterns visible.
"""
        )

        render_penetration_chart(
            penetration
        )

        st.markdown("---")

        render_revenue_penetration_matrix(
            penetration
        )

    with tab3:

        st.markdown(
            """
### AI Intelligence

AI adoption alone does not prove business value.

This section therefore examines both:

**Adoption**
→ How many customers are using AI?

**Economics**
→ How much revenue and gross profit are associated with AI customers?

Together they provide a stronger view of AI commercialisation.
"""
        )

        render_ai_adoption_by_segment(
            ai
        )

        st.markdown("---")

        render_ai_industry_heatmap(
            ai
        )

        st.markdown("---")

        render_ai_economics(
            ai
        )

        st.markdown("---")

        render_ai_customer_value_comparison(
            ai
        )

    with tab4:

        st.markdown(
            """
### Opportunity Explorer

This section looks for **commercial whitespace**.

An industry/segment combination with many non-AI customers and relatively
low AI adoption may represent an expansion opportunity.

This is an analytical prioritisation signal—not a prediction that every
non-AI customer will purchase AI services.
"""
        )

        render_ai_opportunity_table(
            ai
        )

    st.markdown("---")

    with st.expander(
        "📘 Product & AI Metric Dictionary"
    ):

        st.markdown(
            """
### Revenue

**Product Revenue**  
Total revenue attributed to a product.

**Revenue Share %**  
Percentage of total portfolio revenue contributed by the product.

**Revenue Rank**  
Position of the product when products are ordered by revenue.

---

### Adoption

**Customers Using Product**  
Number of unique customers associated with the product.

**Total Customer Base**  
Total customers against which product adoption is measured.

**Customer Penetration %**

```text
Customers Using Product
----------------------------- × 100
Total Customer Base
```
"""
        )