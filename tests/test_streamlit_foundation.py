from __future__ import annotations

import pandas as pd

from src.analytics.data_loader import AnalyticsDataLoader


STREAMLIT_REQUIRED_VIEWS = {
    "v_executive_kpis",
    "v_monthly_revenue",
    "v_regional_performance",
    "v_product_revenue_rank",
    "v_revenue_at_risk",
    "v_business_health_score",
}


def test_streamlit_views_are_approved():

    loader = AnalyticsDataLoader()

    available = set(
        loader.available_views()
    )

    assert STREAMLIT_REQUIRED_VIEWS.issubset(
        available
    )


def test_streamlit_executive_view_loads():

    loader = AnalyticsDataLoader()

    dataframe = loader.load_view(
        "v_executive_kpis"
    )

    assert isinstance(
        dataframe,
        pd.DataFrame,
    )

    assert len(dataframe) == 1


def test_streamlit_monthly_revenue_loads():

    loader = AnalyticsDataLoader()

    dataframe = loader.load_view(
        "v_monthly_revenue"
    )

    assert not dataframe.empty

    assert (
        "net_revenue_usd"
        in dataframe.columns
    )


def test_streamlit_product_ranking_loads():

    loader = AnalyticsDataLoader()

    dataframe = loader.load_view(
        "v_product_revenue_rank"
    )

    assert not dataframe.empty

    required_columns = {
        "product_name",
        "revenue_usd",
        "revenue_rank",
    }

    assert required_columns.issubset(
        dataframe.columns
    )


def test_streamlit_risk_data_loads():

    loader = AnalyticsDataLoader()

    dataframe = loader.load_view(
        "v_revenue_at_risk"
    )

    assert not dataframe.empty

    assert (
        "revenue_at_risk_usd"
        in dataframe.columns
    )


def test_streamlit_business_health_loads():

    loader = AnalyticsDataLoader()

    dataframe = loader.load_view(
        "v_business_health_score"
    )

    assert not dataframe.empty