from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.ml.historical_customer_features import (
    HistoricalCustomerFeatureBuilder,
)
from src.ml.historical_renewal_target import (
    HistoricalRenewalTargetBuilder,
)


@dataclass
class HistoricalTrainingDatasetBundle:
    data: pd.DataFrame
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    observation_cutoff: pd.Timestamp
    prediction_end: pd.Timestamp


class HistoricalCustomerTrainingDatasetBuilder:

    RANDOM_STATE = 42

    # These are outcomes and must NEVER become model inputs.
    TARGET_COLUMNS = {
        "churn_target",
        "future_subscription_state",
        "subscriptions_in_force_at_prediction_end",
        "subscriptions_started_during_followup",
    }

    IDENTIFIER_COLUMNS = {
        "customer_id",
        "customer_name",
        "customer_key",
    }

    def __init__(
        self,
        observation_cutoff: str = "2024-12-31",
        prediction_end: str = "2025-12-31",
    ) -> None:

        self.feature_builder = HistoricalCustomerFeatureBuilder(
            observation_cutoff=observation_cutoff
        )

        self.target_builder = HistoricalRenewalTargetBuilder(
            observation_cutoff=observation_cutoff,
            prediction_end=prediction_end,
        )

    def build(self) -> HistoricalTrainingDatasetBundle:

        feature_bundle = self.feature_builder.build()
        target_bundle = self.target_builder.build()

        features = feature_bundle.features.copy()
        targets = target_bundle.targets.copy()

        data = features.merge(
            targets,
            on="customer_id",
            how="inner",
            validate="one_to_one",
        )

        if data.empty:
            raise ValueError(
                "Historical feature/target merge produced zero rows."
            )

        feature_columns = [
            column
            for column in feature_bundle.feature_columns
            if column not in self.TARGET_COLUMNS
            and column not in self.IDENTIFIER_COLUMNS
        ]

        categorical_features = [
            column
            for column in feature_bundle.categorical_features
            if column in feature_columns
        ]

        numeric_features = [
            column
            for column in feature_columns
            if column not in categorical_features
        ]

        forbidden = (
            self.TARGET_COLUMNS
            | self.IDENTIFIER_COLUMNS
        )

        leakage = sorted(
            set(feature_columns) & forbidden
        )

        if leakage:
            raise ValueError(
                f"Target leakage detected: {leakage}"
            )

        y = data["churn_target"].astype(int)

        if set(y.unique()) != {0, 1}:
            raise ValueError(
                "Training data must contain both churn classes."
            )

        # 70% train, 15% validation, 15% test.
        train_indices, temp_indices = train_test_split(
            np.arange(len(data)),
            test_size=0.30,
            random_state=self.RANDOM_STATE,
            stratify=y,
        )

        temp_y = y.iloc[temp_indices]

        validation_indices, test_indices = train_test_split(
            temp_indices,
            test_size=0.50,
            random_state=self.RANDOM_STATE,
            stratify=temp_y,
        )

        data["dataset_split"] = ""

        data.loc[
            data.index[train_indices],
            "dataset_split",
        ] = "train"

        data.loc[
            data.index[validation_indices],
            "dataset_split",
        ] = "validation"

        data.loc[
            data.index[test_indices],
            "dataset_split",
        ] = "test"

        if (data["dataset_split"] == "").any():
            raise ValueError(
                "Some observations were not assigned a dataset split."
            )

        for split in ("train", "validation", "test"):
            split_classes = set(
                data.loc[
                    data["dataset_split"] == split,
                    "churn_target",
                ].unique()
            )

            if split_classes != {0, 1}:
                raise ValueError(
                    f"{split} split does not contain both classes."
                )

        return HistoricalTrainingDatasetBundle(
            data=data.reset_index(drop=True),
            feature_columns=feature_columns,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            observation_cutoff=feature_bundle.observation_cutoff,
            prediction_end=target_bundle.prediction_end,
        )