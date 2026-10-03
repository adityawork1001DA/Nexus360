from __future__ import annotations

import pandas as pd
import pytest

from src.ml.customer_features import CustomerFeatureBuilder
from src.ml.renewal_target import RenewalTargetBuilder
from src.ml.training_dataset import (
    CustomerTrainingDatasetBuilder,
    TrainingDatasetBundle,
)


@pytest.fixture(scope="module")
def target_bundle():
    return RenewalTargetBuilder().build()


@pytest.fixture(scope="module")
def feature_bundle():
    return CustomerFeatureBuilder().build()


@pytest.fixture(scope="module")
def training_bundle():
    return CustomerTrainingDatasetBuilder().build()


# ============================================================
# RENEWAL / CHURN TARGET
# ============================================================


def test_target_exists(target_bundle):
    assert not target_bundle.targets.empty


def test_target_has_customer_id(target_bundle):
    assert "customer_id" in target_bundle.targets.columns


def test_target_has_one_row_per_customer(target_bundle):
    targets = target_bundle.targets

    assert targets["customer_id"].is_unique


def test_target_customer_ids_not_null(target_bundle):
    targets = target_bundle.targets

    assert targets["customer_id"].notna().all()


def test_target_is_binary(target_bundle):
    values = set(
        target_bundle.targets[
            "churn_target"
        ].unique()
    )

    assert values == {0, 1}


def test_target_contains_both_classes(target_bundle):
    counts = (
        target_bundle.targets[
            "churn_target"
        ].value_counts()
    )

    assert 0 in counts.index
    assert 1 in counts.index
    assert counts.loc[0] > 0
    assert counts.loc[1] > 0


def test_observation_cutoff_exists(target_bundle):
    assert isinstance(
        target_bundle.observation_cutoff,
        pd.Timestamp,
    )


def test_observation_cutoff_matches_target_column(
    target_bundle,
):
    values = pd.to_datetime(
        target_bundle.targets[
            "observation_cutoff"
        ]
    ).unique()

    assert len(values) == 1

    assert pd.Timestamp(
        values[0]
    ) == target_bundle.observation_cutoff


def test_churned_customers_have_no_active_subscription(
    target_bundle,
):
    targets = target_bundle.targets

    churned = targets.loc[
        targets["churn_target"].eq(1)
    ]

    assert (
        churned[
            "active_subscription_count_at_cutoff"
        ]
        == 0
    ).all()


def test_active_customers_have_active_subscription(
    target_bundle,
):
    targets = target_bundle.targets

    active = targets.loc[
        targets["churn_target"].eq(0)
    ]

    assert (
        active[
            "active_subscription_count_at_cutoff"
        ]
        > 0
    ).all()


def test_customer_subscription_state_matches_target(
    target_bundle,
):
    targets = target_bundle.targets

    expected = targets[
        "churn_target"
    ].map(
        {
            0: "Active",
            1: "Churned",
        }
    )

    assert (
        targets[
            "customer_subscription_state"
        ]
        == expected
    ).all()


def test_target_subscription_counts_positive(
    target_bundle,
):
    targets = target_bundle.targets

    assert (
        targets[
            "observed_subscription_count"
        ]
        > 0
    ).all()


def test_target_percentages_valid(target_bundle):
    targets = target_bundle.targets

    columns = [
        "active_subscription_pct_at_cutoff",
        "expired_subscription_pct",
        "active_contract_value_pct",
        "expired_contract_value_pct",
    ]

    for column in columns:
        assert targets[column].between(
            0,
            100,
            inclusive="both",
        ).all()


def test_target_contract_values_non_negative(
    target_bundle,
):
    targets = target_bundle.targets

    columns = [
        "total_contract_value_usd",
        "active_contract_value_usd",
        "expired_contract_value_usd",
    ]

    for column in columns:
        assert (
            targets[column]
            >= 0
        ).all()


# ============================================================
# CUSTOMER FEATURES
# ============================================================


def test_customer_features_exist(feature_bundle):
    assert not feature_bundle.features.empty


def test_customer_features_unique(feature_bundle):
    assert feature_bundle.features[
        "customer_id"
    ].is_unique


def test_customer_feature_lists_exist(feature_bundle):
    assert len(
        feature_bundle.numeric_features
    ) > 0

    assert len(
        feature_bundle.categorical_features
    ) > 0


def test_customer_feature_lists_do_not_overlap(
    feature_bundle,
):
    overlap = (
        set(feature_bundle.numeric_features)
        & set(feature_bundle.categorical_features)
    )

    assert overlap == set()


def test_customer_feature_columns_exist(
    feature_bundle,
):
    expected = (
        set(feature_bundle.numeric_features)
        | set(feature_bundle.categorical_features)
    )

    actual = set(
        feature_bundle.features.columns
    )

    assert expected.issubset(actual)


# ============================================================
# TRAINING DATASET
# ============================================================


def test_training_bundle_type(training_bundle):
    assert isinstance(
        training_bundle,
        TrainingDatasetBundle,
    )


def test_training_dataset_exists(training_bundle):
    assert not training_bundle.data.empty


def test_training_dataset_one_row_per_customer(
    training_bundle,
):
    assert training_bundle.data[
        "customer_id"
    ].is_unique


def test_training_dataset_customer_ids_not_null(
    training_bundle,
):
    assert training_bundle.data[
        "customer_id"
    ].notna().all()


def test_training_target_binary(training_bundle):
    values = set(
        training_bundle.data[
            training_bundle.target_column
        ].unique()
    )

    assert values == {0, 1}


def test_training_target_has_both_classes(
    training_bundle,
):
    counts = (
        training_bundle.data[
            training_bundle.target_column
        ]
        .value_counts()
    )

    assert counts.loc[0] > 0
    assert counts.loc[1] > 0


def test_training_feature_count_positive(
    training_bundle,
):
    assert len(
        training_bundle.feature_columns
    ) > 0


def test_training_features_unique(
    training_bundle,
):
    assert len(
        training_bundle.feature_columns
    ) == len(
        set(
            training_bundle.feature_columns
        )
    )


def test_training_features_exist(
    training_bundle,
):
    assert set(
        training_bundle.feature_columns
    ).issubset(
        training_bundle.data.columns
    )


def test_numeric_features_exist(
    training_bundle,
):
    assert set(
        training_bundle.numeric_features
    ).issubset(
        training_bundle.data.columns
    )


def test_categorical_features_exist(
    training_bundle,
):
    assert set(
        training_bundle.categorical_features
    ).issubset(
        training_bundle.data.columns
    )


def test_numeric_and_categorical_features_disjoint(
    training_bundle,
):
    overlap = (
        set(
            training_bundle.numeric_features
        )
        & set(
            training_bundle.categorical_features
        )
    )

    assert overlap == set()


def test_feature_union_matches_feature_columns(
    training_bundle,
):
    union = (
        set(
            training_bundle.numeric_features
        )
        | set(
            training_bundle.categorical_features
        )
    )

    assert union == set(
        training_bundle.feature_columns
    )


# ============================================================
# LEAKAGE TESTS
# ============================================================


def test_known_leakage_features_removed(
    training_bundle,
):
    leaked = (
        set(
            training_bundle.feature_columns
        )
        & CustomerTrainingDatasetBuilder.LEAKAGE_COLUMNS
    )

    assert leaked == set()


def test_target_not_used_as_feature(
    training_bundle,
):
    assert (
        training_bundle.target_column
        not in training_bundle.feature_columns
    )


def test_target_metadata_not_used_as_features(
    training_bundle,
):
    leaked = (
        set(
            training_bundle.feature_columns
        )
        & CustomerTrainingDatasetBuilder.TARGET_METADATA_COLUMNS
    )

    assert leaked == set()


def test_risk_band_not_used_as_feature(
    training_bundle,
):
    assert (
        "revenue_risk_band"
        not in training_bundle.feature_columns
    )


def test_composite_risk_not_used_as_feature(
    training_bundle,
):
    assert (
        "composite_risk_score"
        not in training_bundle.feature_columns
    )


def test_revenue_at_risk_not_used_as_feature(
    training_bundle,
):
    assert (
        "revenue_at_risk_usd"
        not in training_bundle.feature_columns
    )


def test_renewal_risk_scores_not_used_as_features(
    training_bundle,
):
    forbidden = {
        "avg_renewal_risk_score",
        "max_renewal_risk_score",
        "risk_view_renewal_score",
    }

    assert (
        forbidden
        & set(
            training_bundle.feature_columns
        )
    ) == set()


# ============================================================
# TARGET METADATA
# ============================================================


def test_target_metadata_present(
    training_bundle,
):
    required = {
        "customer_subscription_state",
        "observed_subscription_count_at_cutoff",
        "active_subscription_count_at_cutoff",
        "expired_subscription_count_at_cutoff",
        "total_contract_value_at_cutoff_usd",
        "active_contract_value_at_cutoff_usd",
        "expired_contract_value_at_cutoff_usd",
        "active_subscription_pct_at_cutoff",
        "expired_subscription_pct_at_cutoff",
        "active_contract_value_pct_at_cutoff",
        "expired_contract_value_pct_at_cutoff",
        "observation_cutoff",
    }

    assert required.issubset(
        training_bundle.data.columns
    )


def test_training_churn_state_consistency(
    training_bundle,
):
    data = training_bundle.data

    churned = data.loc[
        data[
            training_bundle.target_column
        ].eq(1)
    ]

    assert (
        churned[
            "active_subscription_count_at_cutoff"
        ]
        == 0
    ).all()


def test_training_active_state_consistency(
    training_bundle,
):
    data = training_bundle.data

    active = data.loc[
        data[
            training_bundle.target_column
        ].eq(0)
    ]

    assert (
        active[
            "active_subscription_count_at_cutoff"
        ]
        > 0
    ).all()


def test_training_target_percentages_valid(
    training_bundle,
):
    data = training_bundle.data

    columns = [
        "active_subscription_pct_at_cutoff",
        "expired_subscription_pct_at_cutoff",
        "active_contract_value_pct_at_cutoff",
        "expired_contract_value_pct_at_cutoff",
    ]

    for column in columns:
        assert data[column].between(
            0,
            100,
            inclusive="both",
        ).all()


# ============================================================
# SPLIT TESTS
# ============================================================


def test_required_splits_exist(
    training_bundle,
):
    splits = set(
        training_bundle.data[
            training_bundle.split_column
        ].unique()
    )

    assert splits == {
        "train",
        "validation",
        "test",
    }


def test_every_split_has_rows(
    training_bundle,
):
    data = training_bundle.data

    for split_name in (
        "train",
        "validation",
        "test",
    ):

        count = (
            data[
                training_bundle.split_column
            ]
            .eq(split_name)
            .sum()
        )

        assert count > 0


def test_every_split_contains_both_classes(
    training_bundle,
):
    data = training_bundle.data

    for split_name in (
        "train",
        "validation",
        "test",
    ):

        subset = data.loc[
            data[
                training_bundle.split_column
            ].eq(split_name)
        ]

        labels = set(
            subset[
                training_bundle.target_column
            ].unique()
        )

        assert labels == {0, 1}


def test_split_proportions(
    training_bundle,
):
    proportions = (
        training_bundle.data[
            training_bundle.split_column
        ]
        .value_counts(
            normalize=True
        )
    )

    assert abs(
        proportions["train"]
        - 0.70
    ) < 0.02

    assert abs(
        proportions["validation"]
        - 0.15
    ) < 0.02

    assert abs(
        proportions["test"]
        - 0.15
    ) < 0.02


def test_split_target_rates_stratified(
    training_bundle,
):
    data = training_bundle.data

    overall_rate = data[
        training_bundle.target_column
    ].mean()

    for split_name in (
        "train",
        "validation",
        "test",
    ):

        split_rate = (
            data.loc[
                data[
                    training_bundle.split_column
                ].eq(split_name),
                training_bundle.target_column,
            ]
            .mean()
        )

        assert abs(
            split_rate
            - overall_rate
        ) < 0.02


def test_customer_appears_in_exactly_one_split(
    training_bundle,
):
    split_counts = (
        training_bundle.data
        .groupby("customer_id")[
            training_bundle.split_column
        ]
        .nunique()
    )

    assert (
        split_counts
        == 1
    ).all()


def test_split_is_reproducible():
    first = (
        CustomerTrainingDatasetBuilder(
            random_state=42
        )
        .build()
        .data[
            [
                "customer_id",
                "dataset_split",
            ]
        ]
        .sort_values(
            "customer_id"
        )
        .reset_index(
            drop=True
        )
    )

    second = (
        CustomerTrainingDatasetBuilder(
            random_state=42
        )
        .build()
        .data[
            [
                "customer_id",
                "dataset_split",
            ]
        ]
        .sort_values(
            "customer_id"
        )
        .reset_index(
            drop=True
        )
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )


# ============================================================
# CONVENIENCE SPLITTER
# ============================================================


def test_split_helper_returns_required_sets(
    training_bundle,
):
    splits = (
        CustomerTrainingDatasetBuilder.split(
            training_bundle
        )
    )

    assert set(
        splits.keys()
    ) == {
        "train",
        "validation",
        "test",
    }


def test_split_helper_feature_shapes(
    training_bundle,
):
    splits = (
        CustomerTrainingDatasetBuilder.split(
            training_bundle
        )
    )

    expected_feature_count = len(
        training_bundle.feature_columns
    )

    for x, y in splits.values():

        assert x.shape[1] == expected_feature_count

        assert len(x) == len(y)


def test_split_helper_columns_match_features(
    training_bundle,
):
    splits = (
        CustomerTrainingDatasetBuilder.split(
            training_bundle
        )
    )

    for x, _ in splits.values():

        assert list(
            x.columns
        ) == training_bundle.feature_columns


def test_split_helper_target_binary(
    training_bundle,
):
    splits = (
        CustomerTrainingDatasetBuilder.split(
            training_bundle
        )
    )

    for _, y in splits.values():

        assert set(
            y.unique()
        ) == {0, 1}