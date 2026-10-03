import numpy as np
import pandas as pd
import pytest

from src.analytics.customer_analysis import CustomerAnalyzer
from src.analytics.data_loader import AnalyticsDataLoader
from src.analytics.profiler import DataProfiler
from src.analytics.statistics import StatisticalAnalyzer


@pytest.fixture(scope="module")
def loader():
    return AnalyticsDataLoader()


def test_analytics_loader_has_28_views(loader):

    assert len(loader.available_views()) == 28


def test_loader_rejects_unknown_view(loader):

    with pytest.raises(ValueError):
        loader.load_view(
            "some_dangerous_random_view"
        )


def test_loader_rejects_invalid_limit(loader):

    with pytest.raises(ValueError):
        loader.load_view(
            "v_monthly_revenue",
            limit=0,
        )


def test_loader_rejects_mutating_query(loader):

    with pytest.raises(ValueError):
        loader.load_query(
            "DELETE FROM warehouse.dim_customer"
        )


def test_monthly_revenue_loads(loader):

    df = loader.load_view(
        "v_monthly_revenue"
    )

    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_customer_360_loads(loader):

    df = loader.load_view(
        "v_customer_360"
    )

    assert not df.empty


def test_revenue_at_risk_loads(loader):

    df = loader.load_view(
        "v_revenue_at_risk"
    )

    assert not df.empty


def test_market_opportunity_loads(loader):

    df = loader.load_view(
        "v_market_opportunity"
    )

    assert not df.empty


def test_business_health_single_row(loader):

    df = loader.load_view(
        "v_business_health_score"
    )

    assert len(df) == 1


def test_profiler_counts_rows():

    df = pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
        }
    )

    profile = DataProfiler().profile(df)

    assert profile["row_count"] == 3
    assert profile["column_count"] == 2


def test_profiler_detects_missing_values():

    df = pd.DataFrame(
        {
            "a": [1, None, 3],
        }
    )

    profile = DataProfiler().profile(df)

    assert profile["missing_cells"] == 1


def test_numeric_summary():

    df = pd.DataFrame(
        {
            "value": [1, 2, 3, 4, 5]
        }
    )

    summary = DataProfiler().numeric_summary(df)

    assert not summary.empty
    assert "mean" in summary.columns


def test_correlation_matrix():

    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 4],
            "y": [2, 4, 6, 8],
        }
    )

    correlation = (
        StatisticalAnalyzer.correlation_matrix(df)
    )

    assert correlation.loc["x", "y"] == pytest.approx(
        1.0
    )


def test_pearson_test():

    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10],
        }
    )

    result = StatisticalAnalyzer.pearson_test(
        df,
        "x",
        "y",
    )

    assert result["correlation"] == pytest.approx(
        1.0
    )


def test_iqr_outlier_detection():

    series = pd.Series(
        [10, 11, 12, 13, 1000]
    )

    result = StatisticalAnalyzer.iqr_outliers(
        series
    )

    assert bool(result.iloc[-1]) is True


def test_z_scores():

    series = pd.Series(
        [1, 2, 3, 4, 5]
    )

    z = StatisticalAnalyzer.z_scores(series)

    assert len(z) == 5
    assert np.isclose(
        z.mean(),
        0.0,
        atol=1e-10,
    )


def test_confidence_interval():

    series = pd.Series(
        [10, 11, 12, 13, 14, 15]
    )

    result = (
        StatisticalAnalyzer
        .confidence_interval_mean(series)
    )

    assert result["lower"] < result["mean"]
    assert result["upper"] > result["mean"]


def test_revenue_risk_scores_are_valid(loader):

    df = loader.load_view(
        "v_revenue_at_risk"
    )

    score = pd.to_numeric(
        df["composite_risk_score"],
        errors="coerce",
    ).dropna()

    assert score.between(
        0,
        100,
    ).all()


def test_revenue_at_risk_non_negative(loader):

    df = loader.load_view(
        "v_revenue_at_risk"
    )

    values = pd.to_numeric(
        df["revenue_at_risk_usd"],
        errors="coerce",
    ).dropna()

    assert (values >= 0).all()


def test_market_opportunity_scores_valid(loader):

    df = loader.load_view(
        "v_market_opportunity"
    )

    score = pd.to_numeric(
        df["market_opportunity_score"],
        errors="coerce",
    ).dropna()

    assert score.between(
        0,
        100,
    ).all()


def test_customer_risk_summary(loader):

    df = loader.load_view(
        "v_revenue_at_risk"
    )

    summary = CustomerAnalyzer.risk_summary(
        df
    )

    assert not summary.empty

    assert (
        summary["customer_count"].sum()
        == len(df)
    )


def test_customer_segment_summary(loader):

    df = loader.load_view(
        "v_revenue_at_risk"
    )

    summary = CustomerAnalyzer.segment_summary(
        df
    )

    assert not summary.empty


def test_business_health_score_valid(loader):

    df = loader.load_view(
        "v_business_health_score"
    )

    score = float(
        df.iloc[0]["business_health_score"]
    )

    assert 0 <= score <= 100


def test_business_health_band_valid(loader):

    df = loader.load_view(
        "v_business_health_score"
    )

    band = df.iloc[0][
        "business_health_band"
    ]

    assert band in {
        "Excellent",
        "Healthy",
        "Watch",
        "At Risk",
        "Critical",
    }