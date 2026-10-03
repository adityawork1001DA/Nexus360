from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analytics.data_loader import AnalyticsDataLoader

from src.ui.components.market import (
    render_country_revenue,
    render_digital_readiness,
    render_fx_exposure_chart,
    render_fx_rate_range,
    render_fx_risk_matrix,
    render_fx_table,
    render_gdp_revenue_matrix,
    render_macro_table,
    render_market_executive_insights,
    render_market_kpis,
    render_market_position_matrix,
    render_opportunity_components,
    render_opportunity_ranking,
    render_opportunity_table,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner=False,
)
def load_market_intelligence_data() -> dict[str, pd.DataFrame]:

    loader = AnalyticsDataLoader()

    return {
        "fx": loader.load_view(
            "v_fx_exposure"
        ),
        "macro": loader.load_view(
            "v_macroeconomic_revenue"
        ),
        "opportunity": loader.load_view(
            "v_market_opportunity"
        ),
    }


# ============================================================
# FILTER HELPERS
# ============================================================

def _safe_options(
    dataframe: pd.DataFrame,
    column: str,
) -> list[str]:

    if column not in dataframe.columns:
        return []

    values = (
        dataframe[column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[
        ~values.str.lower().isin(
            {
                "",
                "none",
                "nan",
                "unknown",
                "unk",
            }
        )
    ]

    return sorted(
        values.unique().tolist()
    )


def _apply_filters(
    fx: pd.DataFrame,
    macro: pd.DataFrame,
    opportunity: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:

    st.sidebar.markdown(
        "### Market Intelligence Filters"
    )

    # --------------------------------------------------------
    # COUNTRY
    # --------------------------------------------------------

    countries = _safe_options(
        macro,
        "country_name",
    )

    selected_countries = (
        st.sidebar.multiselect(
            "Country",
            countries,
            default=countries,
            key="market_country_filter",
        )
    )

    if countries:

        macro = macro[
            macro["country_name"].isin(
                selected_countries
            )
        ].copy()

        opportunity = opportunity[
            opportunity["country_name"].isin(
                selected_countries
            )
        ].copy()

    # --------------------------------------------------------
    # CURRENCY
    # --------------------------------------------------------

    currencies = _safe_options(
        fx,
        "currency_code",
    )

    selected_currencies = (
        st.sidebar.multiselect(
            "Currency",
            currencies,
            default=currencies,
            key="market_currency_filter",
        )
    )

    if currencies:

        fx = fx[
            fx["currency_code"].isin(
                selected_currencies
            )
        ].copy()

    # --------------------------------------------------------
    # FX RISK BAND
    # --------------------------------------------------------

    risk_bands = _safe_options(
        fx,
        "fx_risk_band",
    )

    selected_risk_bands = (
        st.sidebar.multiselect(
            "FX Risk Band",
            risk_bands,
            default=risk_bands,
            key="market_fx_risk_filter",
        )
    )

    if risk_bands:

        fx = fx[
            fx["fx_risk_band"].isin(
                selected_risk_bands
            )
        ].copy()

    # --------------------------------------------------------
    # OPPORTUNITY BAND
    # --------------------------------------------------------

    opportunity_bands = _safe_options(
        opportunity,
        "opportunity_band",
    )

    selected_opportunity_bands = (
        st.sidebar.multiselect(
            "Opportunity Band",
            opportunity_bands,
            default=opportunity_bands,
            key="market_opportunity_band_filter",
        )
    )

    if opportunity_bands:

        opportunity = opportunity[
            opportunity[
                "opportunity_band"
            ].isin(
                selected_opportunity_bands
            )
        ].copy()

    # --------------------------------------------------------
    # MINIMUM OPPORTUNITY SCORE
    # --------------------------------------------------------

    if not opportunity.empty:

        min_score = float(
            opportunity[
                "market_opportunity_score"
            ].min()
        )

        max_score = float(
            opportunity[
                "market_opportunity_score"
            ].max()
        )

        if min_score < max_score:

            selected_min_score = (
                st.sidebar.slider(
                    "Minimum Opportunity Score",
                    min_value=min_score,
                    max_value=max_score,
                    value=min_score,
                    step=0.5,
                    key=(
                        "market_min_opportunity_score"
                    ),
                )
            )

            opportunity = opportunity[
                opportunity[
                    "market_opportunity_score"
                ]
                >= selected_min_score
            ].copy()

    return (
        fx,
        macro,
        opportunity,
    )


# ============================================================
# SCHEMA VALIDATION
# ============================================================

def _validate_bundle(
    bundle: dict[str, pd.DataFrame],
) -> bool:

    required = {

        "fx": [
            "currency_code",
            "currency_name",
            "transaction_count",
            "customer_count",
            "net_revenue_local",
            "net_revenue_usd",
            "revenue_exposure_pct",
            "average_transaction_fx_rate",
            "fx_observation_count",
            "average_market_fx_rate",
            "minimum_fx_rate",
            "maximum_fx_rate",
            "fx_volatility",
            "fx_coefficient_variation_pct",
            "fx_risk_score",
            "fx_risk_band",
            "revenue_exposure_rank",
            "fx_risk_rank",
        ],

        "macro": [
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
        ],

        "opportunity": [
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
            "opportunity_rank",
        ],
    }

    errors: list[str] = []

    for (
        dataset_name,
        required_columns,
    ) in required.items():

        dataframe = bundle.get(
            dataset_name
        )

        if dataframe is None:

            errors.append(
                f"{dataset_name}: dataset missing"
            )

            continue

        missing = [
            column
            for column in required_columns
            if column
            not in dataframe.columns
        ]

        if missing:

            errors.append(
                f"{dataset_name}: missing columns "
                + ", ".join(missing)
            )

    if errors:

        st.error(
            "Market Intelligence schema validation failed."
        )

        for error in errors:
            st.write(
                f"- {error}"
            )

        return False

    return True


# ============================================================
# PAGE
# ============================================================

def render() -> None:

    st.title(
        "Global Market, FX & Macroeconomic Intelligence"
    )

    st.caption(
        "Country economics, currency exposure, AI adoption, "
        "digital readiness and strategic market opportunity."
    )

    st.info(
        """
This command center combines internal commercial performance with
external economic indicators.

It answers five executive questions:

**Currency Risk**
Where is revenue exposed to foreign-exchange movements?

**Economic Position**
How does Nexus revenue compare with the economic scale of each market?

**Digital Readiness**
Which markets combine strong internet penetration with AI potential?

**Commercial Whitespace**
Where is Nexus underpenetrated relative to market characteristics?

**Market Prioritization**
Which countries currently rank highest according to the Nexus 360
market-opportunity framework?
"""
    )

    # ========================================================
    # LOAD
    # ========================================================

    try:

        bundle = (
            load_market_intelligence_data()
        )

    except Exception as exc:

        st.error(
            "Unable to load Market Intelligence data."
        )

        st.exception(exc)

        return

    # ========================================================
    # VALIDATE
    # ========================================================

    if not _validate_bundle(
        bundle
    ):
        return

    fx = bundle["fx"]
    macro = bundle["macro"]
    opportunity = bundle[
        "opportunity"
    ]

    # ========================================================
    # EMPTY CHECK
    # ========================================================

    empty_sources = [
        name
        for name, dataframe
        in bundle.items()
        if dataframe.empty
    ]

    if empty_sources:

        st.warning(
            "The following Market Intelligence datasets "
            "contain no records: "
            + ", ".join(
                empty_sources
            )
        )

        return

    # ========================================================
    # FILTERS
    # ========================================================

    (
        fx,
        macro,
        opportunity,
    ) = _apply_filters(
        fx,
        macro,
        opportunity,
    )

    if (
        fx.empty
        or macro.empty
        or opportunity.empty
    ):

        st.warning(
            "No records match the current "
            "Market Intelligence filters."
        )

        return

    # ========================================================
    # KPI COMMAND CENTER
    # ========================================================

    st.markdown("---")

    st.subheader(
        "Global Market Command Center"
    )

    st.caption(
        "Commercial scale, economic context, digital readiness, "
        "AI adoption and currency risk."
    )

    render_market_kpis(
        fx,
        macro,
        opportunity,
    )

    st.markdown("---")

    # ========================================================
    # TABS
    # ========================================================

    (
        tab_fx,
        tab_macro,
        tab_opportunity,
        tab_strategy,
    ) = st.tabs(
        [
            "FX & Currency Risk",
            "Macroeconomic Intelligence",
            "Market Opportunity",
            "Executive Strategy",
        ]
    )

    # ========================================================
    # FX
    # ========================================================

    with tab_fx:

        st.markdown(
            """
### FX and Currency Risk

International revenue introduces two separate concepts:

**Currency Exposure**

How much business revenue is associated with a currency.

**Currency Volatility**

How much the observed market exchange rate has varied.

A currency becomes more strategically important when meaningful revenue
exposure is combined with meaningful exchange-rate variability.
"""
        )

        render_fx_exposure_chart(
            fx
        )

        st.markdown("---")

        render_fx_risk_matrix(
            fx
        )

        st.markdown("---")

        render_fx_rate_range(
            fx
        )

        st.markdown("---")

        render_fx_table(
            fx
        )

    # ========================================================
    # MACRO
    # ========================================================

    with tab_macro:

        st.markdown(
            """
### Macroeconomic Intelligence

Internal sales data explains what Nexus is currently achieving.

External economic data provides context for what each market looks like.

The analysis combines:

- GDP,
- population,
- GDP per capita,
- internet usage,
- inflation,
- customer count,
- AI adoption,
- revenue,
- gross profit.

The external indicators are sourced through the World Bank ingestion
pipeline already implemented in Nexus 360.
"""
        )

        render_country_revenue(
            macro
        )

        st.markdown("---")

        render_gdp_revenue_matrix(
            macro
        )

        st.markdown("---")

        render_digital_readiness(
            macro
        )

        st.markdown("---")

        render_macro_table(
            macro
        )

    # ========================================================
    # OPPORTUNITY
    # ========================================================

    with tab_opportunity:

        st.markdown(
            """
### Market Opportunity Intelligence

Current revenue does not necessarily identify the best future market.

The Nexus 360 opportunity model therefore evaluates multiple dimensions:

**GDP Score**
Economic scale.

**Wealth Score**
Relative economic purchasing-power signal.

**Digital Score**
Digital-market readiness.

**Whitespace Score**
Commercial room for additional revenue penetration.

**Customer Whitespace Score**
Room for expanding the customer footprint.

These components are combined into the Market Opportunity Score.
"""
        )

        render_opportunity_ranking(
            opportunity
        )

        st.markdown("---")

        render_opportunity_components(
            opportunity
        )

        st.markdown("---")

        render_market_position_matrix(
            opportunity
        )

        st.markdown("---")

        render_opportunity_table(
            opportunity
        )

    # ========================================================
    # STRATEGY
    # ========================================================

    with tab_strategy:

        st.markdown(
            """
### Executive Strategy Signals

This section translates market analytics into management-level signals.

The objective is not to automatically decide where Nexus should invest.

Instead, the dashboard highlights markets and currencies that deserve
additional human analysis.
"""
        )

        render_market_executive_insights(
            fx,
            macro,
            opportunity,
        )

    # ========================================================
    # METRIC DICTIONARY
    # ========================================================

    st.markdown("---")

    with st.expander(
        "Market Intelligence Metric Dictionary"
    ):

        st.markdown(
            """
### Revenue Exposure %

```text
Currency Revenue
---------------- x 100
Total Revenue
```
"""
        )