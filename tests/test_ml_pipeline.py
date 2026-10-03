from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.ml.historical_training_dataset import (
    HistoricalCustomerTrainingDatasetBuilder,
)
from src.ml.current_customer_features import (
    CurrentCustomerFeatureBuilder,
)


ARTIFACT_DIR = Path("artifacts/ml")

SCORES_PATH = ARTIFACT_DIR / "current_customer_churn_scores.csv"
SUMMARY_PATH = ARTIFACT_DIR / "current_churn_summary.json"
METRICS_PATH = ARTIFACT_DIR / "historical_model_metrics.json"
IMPORTANCE_PATH = ARTIFACT_DIR / "historical_feature_importance.csv"


@pytest.fixture(scope="module")
def historical_bundle():
    return HistoricalCustomerTrainingDatasetBuilder().build()


@pytest.fixture(scope="module")
def historical_data(historical_bundle):
    return historical_bundle.data


@pytest.fixture(scope="module")
def current_bundle():
    return CurrentCustomerFeatureBuilder().build()


@pytest.fixture(scope="module")
def current_data(current_bundle):
    return current_bundle.features


@pytest.fixture(scope="module")
def scores():
    assert SCORES_PATH.exists(), (
        "Current churn scores do not exist. "
        "Run: python -m scripts.predict_current_churn"
    )
    return pd.read_csv(SCORES_PATH)


@pytest.fixture(scope="module")
def summary():
    assert SUMMARY_PATH.exists()
    with SUMMARY_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="module")
def metrics():
    assert METRICS_PATH.exists()
    with METRICS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_historical_dataset_exists(historical_data):
    assert len(historical_data) > 0


def test_historical_target_has_two_classes(historical_data):
    assert set(historical_data["churn_target"].unique()) == {0, 1}


def test_historical_target_not_null(historical_data):
    assert historical_data["churn_target"].notna().all()


def test_dataset_splits_exist(historical_data):
    assert set(
        historical_data["dataset_split"].unique()
    ) == {"train", "validation", "test"}


def test_each_split_has_both_classes(historical_data):
    for _, frame in historical_data.groupby("dataset_split"):
        assert frame["churn_target"].nunique() == 2


def test_customer_ids_unique(historical_data):
    assert not historical_data["customer_id"].duplicated().any()


def test_no_future_customer_signup(historical_bundle, historical_data):
    signup = pd.to_datetime(historical_data["signup_date"])
    assert (
        signup <= historical_bundle.observation_cutoff
    ).all()


def test_current_features_exist(current_data):
    assert len(current_data) > 0


def test_current_customer_ids_unique(current_data):
    assert not current_data["customer_id"].duplicated().any()


def test_current_customers_have_active_subscription(current_data):
    assert (
        current_data["subscriptions_in_force_at_cutoff"] > 0
    ).all()


def test_training_serving_feature_schema_matches(
    historical_bundle,
    current_bundle,
):
    assert set(historical_bundle.feature_columns) == set(
        current_bundle.feature_columns
    )


def test_training_serving_feature_order_matches(
    historical_bundle,
    current_bundle,
):
    assert historical_bundle.feature_columns == (
        current_bundle.feature_columns
    )


def test_no_infinite_historical_features(
    historical_bundle,
    historical_data,
):
    numeric = historical_data[
        historical_bundle.numeric_features
    ].apply(pd.to_numeric, errors="coerce")

    assert np.isfinite(
        numeric.fillna(0).to_numpy(dtype=float)
    ).all()


def test_no_infinite_current_features(
    current_bundle,
    current_data,
):
    numeric = current_data[
        current_bundle.numeric_features
    ].apply(pd.to_numeric, errors="coerce")

    assert np.isfinite(
        numeric.fillna(0).to_numpy(dtype=float)
    ).all()


def test_current_scores_exist(scores):
    assert len(scores) > 0


def test_score_count_matches_current_population(scores, current_data):
    assert len(scores) == len(current_data)


def test_score_customer_ids_unique(scores):
    assert not scores["customer_id"].duplicated().any()


def test_churn_probability_valid(scores):
    assert scores["churn_probability"].between(0, 1).all()


def test_churn_probability_pct_valid(scores):
    assert scores["churn_probability_pct"].between(0, 100).all()


def test_predicted_churn_binary(scores):
    assert set(scores["predicted_churn"].unique()).issubset({0, 1})


def test_risk_bands_valid(scores):
    allowed = {"Low", "Medium", "High", "Critical"}
    assert set(scores["risk_band"].unique()).issubset(allowed)


def test_contract_value_non_negative(scores):
    assert (
        scores["contract_value_in_force_at_cutoff"] >= 0
    ).all()


def test_expected_contract_value_at_risk_non_negative(scores):
    assert (
        scores["expected_contract_value_at_risk_usd"] >= 0
    ).all()


def test_expected_value_at_risk_formula(scores):
    expected = (
        scores["contract_value_in_force_at_cutoff"]
        * scores["churn_probability"]
    )

    assert np.allclose(
        scores["expected_contract_value_at_risk_usd"],
        expected,
        rtol=1e-5,
        atol=0.02,
    )


def test_summary_customer_count(summary, scores):
    assert summary["customers_scored"] == len(scores)


def test_summary_predicted_churn_count(summary, scores):
    assert summary["predicted_churn_customers"] == int(
        scores["predicted_churn"].sum()
    )


def test_summary_predicted_churn_rate(summary, scores):
    expected = round(
        scores["predicted_churn"].mean() * 100,
        2,
    )

    assert summary["predicted_churn_rate_pct"] == pytest.approx(
        expected,
        abs=0.01,
    )


def test_summary_average_probability(summary, scores):
    expected = round(
        scores["churn_probability"].mean() * 100,
        2,
    )

    assert summary[
        "average_churn_probability_pct"
    ] == pytest.approx(expected, abs=0.01)


def test_summary_expected_value_at_risk(summary, scores):
    expected = scores[
        "expected_contract_value_at_risk_usd"
    ].sum()

    assert summary[
        "expected_contract_value_at_risk_usd"
    ] == pytest.approx(expected, abs=1.0)


def test_decision_threshold_valid(summary):
    assert 0 < summary["decision_threshold"] < 1


def test_metrics_have_validation_and_test(metrics):
    assert "validation" in metrics
    assert "test" in metrics


@pytest.mark.parametrize(
    "metric",
    [
        "roc_auc",
        "pr_auc",
        "accuracy",
        "precision",
        "recall",
        "f1",
    ],
)
def test_test_metrics_valid(metrics, metric):
    value = metrics["test"][metric]
    assert 0 <= value <= 1


def test_test_confusion_matrix_valid(metrics):
    test = metrics["test"]

    total = (
        test["tn"]
        + test["fp"]
        + test["fn"]
        + test["tp"]
    )

    assert total > 0


def test_feature_importance_exists():
    assert IMPORTANCE_PATH.exists()

    importance = pd.read_csv(IMPORTANCE_PATH)

    assert len(importance) > 0
    assert "feature" in importance.columns
    assert "importance" in importance.columns


def test_feature_importance_finite():
    importance = pd.read_csv(IMPORTANCE_PATH)

    values = pd.to_numeric(
        importance["importance"],
        errors="coerce",
    )

    assert values.notna().all()
    assert np.isfinite(values).all()


def test_rolling_revenue_drift_not_extreme(
    historical_data,
    current_data,
):
    historical_mean = historical_data[
        "trailing_revenue_usd"
    ].mean()

    current_mean = current_data[
        "trailing_revenue_usd"
    ].mean()

    ratio = current_mean / historical_mean

    assert 0.25 <= ratio <= 4.0


def test_rolling_support_drift_not_extreme(
    historical_data,
    current_data,
):
    historical_mean = historical_data[
        "trailing_support_tickets"
    ].mean()

    current_mean = current_data[
        "trailing_support_tickets"
    ].mean()

    ratio = current_mean / historical_mean

    assert 0.25 <= ratio <= 4.0