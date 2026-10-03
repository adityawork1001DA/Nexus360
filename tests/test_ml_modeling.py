from __future__ import annotations

import numpy as np
import pytest

from src.ml.churn_model import ChurnModelTrainer
from src.ml.churn_scoring import CustomerChurnScorer


# ---------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def model_bundle():
    """
    Train/build the complete historical churn model once for this
    test module.
    """
    return ChurnModelTrainer().build()


@pytest.fixture(scope="module")
def training_data(model_bundle):
    """
    Historical point-in-time training dataset used by the model.
    """
    return model_bundle.training_data


@pytest.fixture(scope="module")
def scores(model_bundle):
    """
    Historical customer churn scores generated from the trained model.
    """
    return CustomerChurnScorer(
        model_bundle
    ).score()


# ---------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------


def test_model_trains(model_bundle):
    assert model_bundle.pipeline is not None


def test_model_name_exists(model_bundle):
    assert model_bundle.model_name in {
        "logistic_regression",
        "random_forest",
        "hist_gradient_boosting",
    }


def test_threshold_valid(model_bundle):
    assert 0 < model_bundle.threshold < 1


# ---------------------------------------------------------------------
# Feature schema
# ---------------------------------------------------------------------


def test_feature_count(model_bundle):
    assert len(model_bundle.feature_columns) > 0


def test_expected_feature_count(model_bundle):
    """
    Current production historical model contract.

    The rolling-window / point-in-time feature engineering pipeline
    currently exposes 41 model features.
    """
    assert len(model_bundle.feature_columns) == 41


def test_feature_columns_unique(model_bundle):
    assert len(
        model_bundle.feature_columns
    ) == len(
        set(model_bundle.feature_columns)
    )


def test_target_not_feature(model_bundle):
    assert (
        "churn_target"
        not in model_bundle.feature_columns
    )


def test_dataset_split_not_feature(model_bundle):
    assert (
        "dataset_split"
        not in model_bundle.feature_columns
    )


def test_customer_id_not_feature(model_bundle):
    assert (
        "customer_id"
        not in model_bundle.feature_columns
    )


def test_customer_name_not_feature(model_bundle):
    assert (
        "customer_name"
        not in model_bundle.feature_columns
    )


# ---------------------------------------------------------------------
# Historical training dataset
# ---------------------------------------------------------------------


def test_training_rows(training_data):
    """
    Avoid hard-coding historical population size.

    Customer eligibility can legitimately change if the warehouse is
    refreshed or the historical observation cutoff changes.
    """
    assert len(training_data) > 0


def test_training_customer_ids_unique(training_data):
    assert training_data[
        "customer_id"
    ].is_unique


def test_training_customer_ids_not_null(training_data):
    assert training_data[
        "customer_id"
    ].notna().all()


def test_target_exists(training_data):
    assert "churn_target" in training_data.columns


def test_target_not_null(training_data):
    assert training_data[
        "churn_target"
    ].notna().all()


def test_target_binary(training_data):
    assert set(
        training_data[
            "churn_target"
        ].unique()
    ) == {0, 1}


def test_dataset_split_exists(training_data):
    assert (
        "dataset_split"
        in training_data.columns
    )


def test_split_counts(training_data):
    """
    Validate split integrity without depending on a frozen number of
    warehouse rows.
    """
    counts = (
        training_data[
            "dataset_split"
        ]
        .value_counts()
    )

    assert set(counts.index) == {
        "train",
        "validation",
        "test",
    }

    assert counts.sum() == len(
        training_data
    )

    assert (counts > 0).all()


def test_each_split_has_both_target_classes(
    training_data,
):
    """
    Classification evaluation requires both churned and retained
    customers in every dataset split.
    """
    for split_name in [
        "train",
        "validation",
        "test",
    ]:
        split = training_data.loc[
            training_data[
                "dataset_split"
            ]
            == split_name
        ]

        assert split[
            "churn_target"
        ].nunique() == 2


def test_model_features_exist_in_training_data(
    model_bundle,
    training_data,
):
    missing = set(
        model_bundle.feature_columns
    ) - set(
        training_data.columns
    )

    assert not missing


# ---------------------------------------------------------------------
# Validation metrics
# ---------------------------------------------------------------------


def test_validation_roc_auc_valid(model_bundle):
    assert (
        0
        <= model_bundle.validation_metrics.roc_auc
        <= 1
    )


def test_validation_pr_auc_valid(model_bundle):
    assert (
        0
        <= model_bundle.validation_metrics.pr_auc
        <= 1
    )


def test_validation_precision_valid(model_bundle):
    assert (
        0
        <= model_bundle.validation_metrics.precision
        <= 1
    )


def test_validation_recall_valid(model_bundle):
    assert (
        0
        <= model_bundle.validation_metrics.recall
        <= 1
    )


def test_validation_f1_valid(model_bundle):
    assert (
        0
        <= model_bundle.validation_metrics.f1
        <= 1
    )


def test_validation_accuracy_valid(model_bundle):
    assert (
        0
        <= model_bundle.validation_metrics.accuracy
        <= 1
    )


# ---------------------------------------------------------------------
# Untouched test metrics
# ---------------------------------------------------------------------


def test_test_roc_auc_valid(model_bundle):
    assert (
        0
        <= model_bundle.test_metrics.roc_auc
        <= 1
    )


def test_test_pr_auc_valid(model_bundle):
    assert (
        0
        <= model_bundle.test_metrics.pr_auc
        <= 1
    )


def test_precision_valid(model_bundle):
    assert (
        0
        <= model_bundle.test_metrics.precision
        <= 1
    )


def test_recall_valid(model_bundle):
    assert (
        0
        <= model_bundle.test_metrics.recall
        <= 1
    )


def test_f1_valid(model_bundle):
    assert (
        0
        <= model_bundle.test_metrics.f1
        <= 1
    )


def test_accuracy_valid(model_bundle):
    assert (
        0
        <= model_bundle.test_metrics.accuracy
        <= 1
    )


def test_confusion_matrix_values_non_negative(
    model_bundle,
):
    metrics = model_bundle.test_metrics

    assert metrics.tn >= 0
    assert metrics.fp >= 0
    assert metrics.fn >= 0
    assert metrics.tp >= 0


def test_confusion_matrix_total(
    model_bundle,
    training_data,
):
    """
    Confusion-matrix observations must exactly equal the number of
    customers in the untouched test split.

    This replaces the old hard-coded 375-row assumption.
    """
    metrics = model_bundle.test_metrics

    total = (
        metrics.tn
        + metrics.fp
        + metrics.fn
        + metrics.tp
    )

    expected = int(
        (
            training_data[
                "dataset_split"
            ]
            == "test"
        ).sum()
    )

    assert total == expected


# ---------------------------------------------------------------------
# Historical customer scoring
# ---------------------------------------------------------------------


def test_scores_exist(
    scores,
    training_data,
):
    """
    Historical scoring should produce exactly one score for every
    eligible historical customer.
    """
    assert len(scores) > 0

    assert len(scores) == len(
        training_data
    )


def test_score_customer_unique(scores):
    assert scores[
        "customer_id"
    ].is_unique


def test_score_customer_not_null(scores):
    assert scores[
        "customer_id"
    ].notna().all()


def test_probabilities_valid(scores):
    assert scores[
        "churn_probability"
    ].between(
        0,
        1,
    ).all()


def test_probability_percentage_valid(scores):
    assert scores[
        "churn_probability_pct"
    ].between(
        0,
        100,
    ).all()


def test_probability_percentage_matches_probability(
    scores,
):
    expected = (
        scores[
            "churn_probability"
        ]
        * 100
    )

    actual = scores[
        "churn_probability_pct"
    ]

    assert np.allclose(
        actual,
        expected,
        atol=0.01,
    )


def test_probability_finite(scores):
    assert np.isfinite(
        scores[
            "churn_probability"
        ]
    ).all()


def test_probability_percentage_finite(scores):
    assert np.isfinite(
        scores[
            "churn_probability_pct"
        ]
    ).all()


# ---------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------


def test_predictions_binary(scores):
    assert set(
        scores[
            "churn_prediction"
        ].unique()
    ).issubset(
        {
            0,
            1,
        }
    )


def test_predictions_not_null(scores):
    assert scores[
        "churn_prediction"
    ].notna().all()


# ---------------------------------------------------------------------
# Risk bands
# ---------------------------------------------------------------------


def test_risk_bands_valid(scores):
    assert set(
        scores[
            "risk_band"
        ].unique()
    ).issubset(
        {
            "Low",
            "Medium",
            "High",
            "Critical",
        }
    )


def test_risk_bands_not_null(scores):
    assert scores[
        "risk_band"
    ].notna().all()


# ---------------------------------------------------------------------
# Risk ranking
# ---------------------------------------------------------------------


def test_risk_rank_valid(scores):
    assert scores[
        "risk_rank"
    ].min() == 1

    assert scores[
        "risk_rank"
    ].max() == len(
        scores
    )


def test_risk_rank_unique(scores):
    assert scores[
        "risk_rank"
    ].is_unique


def test_scores_sorted(scores):
    """
    Historical score output must be ordered from highest to lowest
    churn probability.
    """
    values = scores[
        "churn_probability"
    ].to_numpy()

    assert np.all(
        values[:-1]
        >= values[1:]
    )


def test_risk_rank_matches_sort_order(scores):
    expected = np.arange(
        1,
        len(scores) + 1,
    )

    actual = scores[
        "risk_rank"
    ].to_numpy()

    assert np.array_equal(
        actual,
        expected,
    )


# ---------------------------------------------------------------------
# Revenue / financial risk
# ---------------------------------------------------------------------


def test_revenue_at_risk_non_negative(scores):
    if (
        "model_revenue_at_risk_usd"
        in scores.columns
    ):
        assert (
            scores[
                "model_revenue_at_risk_usd"
            ]
            >= 0
        ).all()


def test_revenue_at_risk_finite(scores):
    if (
        "model_revenue_at_risk_usd"
        in scores.columns
    ):
        assert np.isfinite(
            scores[
                "model_revenue_at_risk_usd"
            ].fillna(0)
        ).all()


# ---------------------------------------------------------------------
# Final structural sanity checks
# ---------------------------------------------------------------------


def test_no_duplicate_score_rows(scores):
    assert not scores.duplicated(
        subset=["customer_id"]
    ).any()


def test_score_population_matches_training_population(
    scores,
    training_data,
):
    score_customers = set(
        scores[
            "customer_id"
        ]
    )

    training_customers = set(
        training_data[
            "customer_id"
        ]
    )

    assert (
        score_customers
        == training_customers
    )