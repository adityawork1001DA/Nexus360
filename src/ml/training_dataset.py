from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split

from src.ml.customer_features import CustomerFeatureBuilder
from src.ml.renewal_target import RenewalTargetBuilder


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainingDatasetBundle:
    """
    Final supervised customer churn dataset.

    data
        Full customer-level dataset containing identifiers,
        model features, target metadata, target, and split.

    feature_columns
        Ordered model-input columns.

    numeric_features
        Numeric model-input columns.

    categorical_features
        Categorical model-input columns.

    target_column
        Binary target column.

    split_column
        Train / validation / test assignment.
    """

    data: pd.DataFrame
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    target_column: str
    split_column: str


class CustomerTrainingDatasetBuilder:
    """
    Build the Nexus 360 customer-state classification dataset.

    Target
    ------
    churn_target = 1
        Customer has no active/in-force subscription at the
        observation cutoff.

    churn_target = 0
        Customer has at least one active/in-force subscription
        at the observation cutoff.

    Split strategy
    --------------
    Stratified customer-level split:

        train       70%
        validation  15%
        test        15%

    Why stratified rather than temporal?
    ------------------------------------
    The target represents customer state at a single observation
    snapshot. It is not a historical future-event label.

    A chronological split based on subscription start date caused
    severe target drift because newer customers were overwhelmingly
    active at the snapshot cutoff.

    Stratification preserves the overall class distribution while
    maintaining completely disjoint customer sets.

    Leakage controls
    ----------------
    Existing semantic risk scores and target-construction fields are
    explicitly excluded from model inputs.
    """

    TARGET_COLUMN = "churn_target"
    SPLIT_COLUMN = "dataset_split"

    RANDOM_STATE = 42
    TEST_SIZE = 0.15

    # After reserving 15% for test, 85% remains.
    # 15 / 85 gives another 15% of the original dataset.
    VALIDATION_SIZE_WITHIN_REMAINDER = 0.15 / 0.85

    LEAKAGE_COLUMNS = {
        # Semantic-layer risk outputs
        "avg_renewal_risk_score",
        "max_renewal_risk_score",
        "high_risk_subscription_count",
        "critical_risk_subscription_count",
        "composite_risk_score",
        "revenue_at_risk_usd",
        "risk_view_renewal_score",
        "revenue_risk_band",

        # Defensive target-state exclusions
        "churn_target",
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

    TARGET_RENAME_MAP = {
        "observed_subscription_count":
            "observed_subscription_count_at_cutoff",

        "expired_subscription_count":
            "expired_subscription_count_at_cutoff",

        "total_contract_value_usd":
            "total_contract_value_at_cutoff_usd",

        "active_contract_value_usd":
            "active_contract_value_at_cutoff_usd",

        "expired_contract_value_usd":
            "expired_contract_value_at_cutoff_usd",

        "expired_subscription_pct":
            "expired_subscription_pct_at_cutoff",

        "active_contract_value_pct":
            "active_contract_value_pct_at_cutoff",

        "expired_contract_value_pct":
            "expired_contract_value_pct_at_cutoff",
    }

    TARGET_METADATA_COLUMNS = {
        "churn_target",
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
        "earliest_subscription_start_date",
        "latest_subscription_start_date",
        "earliest_subscription_end_date",
        "latest_subscription_end_date",
        "observation_cutoff",
    }

    def __init__(
        self,
        observation_cutoff: str | pd.Timestamp | None = None,
        random_state: int = RANDOM_STATE,
    ) -> None:

        self.feature_builder = CustomerFeatureBuilder()

        self.target_builder = RenewalTargetBuilder(
            observation_cutoff=observation_cutoff
        )

        self.random_state = random_state

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build(self) -> TrainingDatasetBundle:
        """
        Build and validate the complete supervised ML dataset.
        """

        logger.info(
            "Building customer ML features."
        )

        feature_bundle = self.feature_builder.build()

        logger.info(
            "Building customer churn target."
        )

        target_bundle = self.target_builder.build()

        features = feature_bundle.features.copy()
        targets = target_bundle.targets.copy()

        self._validate_pre_merge_sources(
            features=features,
            targets=targets,
        )

        # ----------------------------------------------------
        # Rename target-side metadata to prevent collisions
        # with legitimate predictive feature names.
        # ----------------------------------------------------

        targets = targets.rename(
            columns=self.TARGET_RENAME_MAP
        )

        target_columns = [
            "customer_id",
            "churn_target",
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
            "earliest_subscription_start_date",
            "latest_subscription_start_date",
            "earliest_subscription_end_date",
            "latest_subscription_end_date",
            "observation_cutoff",
        ]

        missing_target_columns = sorted(
            set(target_columns)
            - set(targets.columns)
        )

        if missing_target_columns:
            raise ValueError(
                "Target dataset is missing required columns: "
                + ", ".join(missing_target_columns)
            )

        # ----------------------------------------------------
        # Prevent silent Pandas _x / _y suffixing.
        # ----------------------------------------------------

        target_payload = (
            set(target_columns)
            - {"customer_id"}
        )

        collisions = sorted(
            set(features.columns)
            & target_payload
        )

        if collisions:
            raise ValueError(
                "Feature/target column collision detected: "
                + ", ".join(collisions)
            )

        # ----------------------------------------------------
        # One customer -> one target
        # ----------------------------------------------------

        data = features.merge(
            targets[target_columns],
            how="inner",
            on="customer_id",
            validate="one_to_one",
        )

        if data.empty:
            raise ValueError(
                "No customers matched between features and targets."
            )

        # ----------------------------------------------------
        # Model feature selection
        # ----------------------------------------------------

        numeric_features = [
            column
            for column in feature_bundle.numeric_features
            if column not in self.LEAKAGE_COLUMNS
        ]

        categorical_features = [
            column
            for column in feature_bundle.categorical_features
            if column not in self.LEAKAGE_COLUMNS
        ]

        feature_columns = [
            *numeric_features,
            *categorical_features,
        ]

        self._validate_feature_definition(
            data=data,
            feature_columns=feature_columns,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
        )

        # ----------------------------------------------------
        # Stratified train / validation / test split
        # ----------------------------------------------------

        data = self._assign_stratified_split(
            data
        )

        # ----------------------------------------------------
        # Final integrity checks
        # ----------------------------------------------------

        self._validate_dataset(
            data=data,
            feature_columns=feature_columns,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
        )

        logger.info(
            "Training dataset built: %s rows, %s features.",
            len(data),
            len(feature_columns),
        )

        logger.info(
            "Split counts: %s",
            data[
                self.SPLIT_COLUMN
            ].value_counts().to_dict(),
        )

        logger.info(
            "Target counts: %s",
            data[
                self.TARGET_COLUMN
            ].value_counts().to_dict(),
        )

        return TrainingDatasetBundle(
            data=data,
            feature_columns=feature_columns,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            target_column=self.TARGET_COLUMN,
            split_column=self.SPLIT_COLUMN,
        )

    # ========================================================
    # PRE-MERGE VALIDATION
    # ========================================================

    @staticmethod
    def _validate_pre_merge_sources(
        features: pd.DataFrame,
        targets: pd.DataFrame,
    ) -> None:

        if features.empty:
            raise ValueError(
                "Customer feature dataset contains no rows."
            )

        if targets.empty:
            raise ValueError(
                "Customer target dataset contains no rows."
            )

        for name, dataframe in (
            ("feature", features),
            ("target", targets),
        ):

            if "customer_id" not in dataframe.columns:
                raise ValueError(
                    f"Customer {name} dataset is missing customer_id."
                )

            if dataframe["customer_id"].isna().any():
                raise ValueError(
                    f"Customer {name} dataset contains "
                    "null customer_id values."
                )

            if dataframe["customer_id"].duplicated().any():
                raise ValueError(
                    f"Customer {name} dataset must contain "
                    "one row per customer."
                )

    # ========================================================
    # FEATURE VALIDATION
    # ========================================================

    def _validate_feature_definition(
        self,
        data: pd.DataFrame,
        feature_columns: list[str],
        numeric_features: list[str],
        categorical_features: list[str],
    ) -> None:

        if not feature_columns:
            raise ValueError(
                "No model features were selected."
            )

        if len(feature_columns) != len(
            set(feature_columns)
        ):
            duplicates = sorted(
                {
                    column
                    for column in feature_columns
                    if feature_columns.count(column) > 1
                }
            )

            raise ValueError(
                "Duplicate model features detected: "
                + ", ".join(duplicates)
            )

        missing = sorted(
            set(feature_columns)
            - set(data.columns)
        )

        if missing:
            raise ValueError(
                "Training dataset is missing features: "
                + ", ".join(missing)
            )

        overlap = (
            set(numeric_features)
            & set(categorical_features)
        )

        if overlap:
            raise ValueError(
                "Features cannot be both numeric and categorical: "
                + ", ".join(sorted(overlap))
            )

        expected = (
            set(numeric_features)
            | set(categorical_features)
        )

        if expected != set(feature_columns):
            raise ValueError(
                "feature_columns is inconsistent with numeric "
                "and categorical feature definitions."
            )

        leaked = (
            set(feature_columns)
            & self.LEAKAGE_COLUMNS
        )

        if leaked:
            raise ValueError(
                "Leakage features reached model inputs: "
                + ", ".join(sorted(leaked))
            )

        target_leakage = (
            set(feature_columns)
            & self.TARGET_METADATA_COLUMNS
        )

        if target_leakage:
            raise ValueError(
                "Target-construction metadata reached model inputs: "
                + ", ".join(sorted(target_leakage))
            )

    # ========================================================
    # STRATIFIED SPLIT
    # ========================================================

    def _assign_stratified_split(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Create deterministic customer-level stratified splits.

        Final proportions are approximately:

            train       70%
            validation  15%
            test        15%

        All splitting occurs at customer grain because the dataset
        already contains exactly one row per customer.
        """

        data = dataframe.copy()

        target = data[self.TARGET_COLUMN]

        class_counts = target.value_counts()

        if len(class_counts) != 2:
            raise ValueError(
                "Stratified splitting requires exactly "
                "two target classes."
            )

        if class_counts.min() < 3:
            raise ValueError(
                "Each target class requires at least three "
                "observations for train/validation/test splitting."
            )

        # ----------------------------------------------------
        # Stage 1:
        # 85% train+validation
        # 15% test
        # ----------------------------------------------------

        remainder, test = train_test_split(
            data,
            test_size=self.TEST_SIZE,
            random_state=self.random_state,
            stratify=data[self.TARGET_COLUMN],
            shuffle=True,
        )

        # ----------------------------------------------------
        # Stage 2:
        # Split the remaining 85% into:
        #
        # 70% original -> train
        # 15% original -> validation
        # ----------------------------------------------------

        train, validation = train_test_split(
            remainder,
            test_size=self.VALIDATION_SIZE_WITHIN_REMAINDER,
            random_state=self.random_state,
            stratify=remainder[self.TARGET_COLUMN],
            shuffle=True,
        )

        train = train.copy()
        validation = validation.copy()
        test = test.copy()

        train[self.SPLIT_COLUMN] = "train"
        validation[self.SPLIT_COLUMN] = "validation"
        test[self.SPLIT_COLUMN] = "test"

        result = pd.concat(
            [
                train,
                validation,
                test,
            ],
            axis=0,
            ignore_index=True,
        )

        # Stable final ordering makes exports/tests reproducible.
        split_order = pd.Categorical(
            result[self.SPLIT_COLUMN],
            categories=[
                "train",
                "validation",
                "test",
            ],
            ordered=True,
        )

        result = (
            result
            .assign(
                _split_order=split_order
            )
            .sort_values(
                [
                    "_split_order",
                    "customer_id",
                ]
            )
            .drop(
                columns="_split_order"
            )
            .reset_index(
                drop=True
            )
        )

        return result

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    def _validate_dataset(
        self,
        data: pd.DataFrame,
        feature_columns: list[str],
        numeric_features: list[str],
        categorical_features: list[str],
    ) -> None:

        if data.empty:
            raise ValueError(
                "Training dataset contains no rows."
            )

        if data["customer_id"].isna().any():
            raise ValueError(
                "Training dataset contains null customer_id."
            )

        if data["customer_id"].duplicated().any():
            raise ValueError(
                "Training dataset must contain exactly "
                "one row per customer."
            )

        self._validate_feature_definition(
            data=data,
            feature_columns=feature_columns,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
        )

        # ----------------------------------------------------
        # Binary target
        # ----------------------------------------------------

        if data[
            self.TARGET_COLUMN
        ].isna().any():
            raise ValueError(
                "Training dataset contains null target values."
            )

        labels = set(
            data[
                self.TARGET_COLUMN
            ].unique()
        )

        if labels != {0, 1}:
            counts = (
                data[
                    self.TARGET_COLUMN
                ]
                .value_counts(
                    dropna=False
                )
                .to_dict()
            )

            raise ValueError(
                "Training dataset requires target classes "
                "0 and 1. "
                f"Observed: {counts}"
            )

        # ----------------------------------------------------
        # Split existence
        # ----------------------------------------------------

        expected_splits = {
            "train",
            "validation",
            "test",
        }

        actual_splits = set(
            data[
                self.SPLIT_COLUMN
            ].unique()
        )

        if actual_splits != expected_splits:
            raise ValueError(
                "Expected train, validation and test splits. "
                f"Found: {sorted(actual_splits)}"
            )

        # ----------------------------------------------------
        # Every split must contain both classes.
        # ----------------------------------------------------

        for split_name in (
            "train",
            "validation",
            "test",
        ):

            subset = data.loc[
                data[
                    self.SPLIT_COLUMN
                ].eq(split_name)
            ]

            if subset.empty:
                raise ValueError(
                    f"{split_name} split contains no rows."
                )

            split_labels = set(
                subset[
                    self.TARGET_COLUMN
                ].unique()
            )

            if split_labels != {0, 1}:
                raise ValueError(
                    f"{split_name} split does not contain "
                    "both target classes."
                )

        # ----------------------------------------------------
        # Split proportions
        # ----------------------------------------------------

        split_proportions = (
            data[
                self.SPLIT_COLUMN
            ]
            .value_counts(
                normalize=True
            )
        )

        expected_proportions = {
            "train": 0.70,
            "validation": 0.15,
            "test": 0.15,
        }

        for split_name, expected in (
            expected_proportions.items()
        ):

            actual = float(
                split_proportions[
                    split_name
                ]
            )

            # Rounding caused by integer customer counts is allowed.
            if abs(actual - expected) > 0.02:
                raise ValueError(
                    f"{split_name} split proportion "
                    f"{actual:.4f} differs materially from "
                    f"expected {expected:.4f}."
                )

        # ----------------------------------------------------
        # Stratification quality
        # ----------------------------------------------------

        overall_rate = float(
            data[
                self.TARGET_COLUMN
            ].mean()
        )

        for split_name in (
            "train",
            "validation",
            "test",
        ):

            subset = data.loc[
                data[
                    self.SPLIT_COLUMN
                ].eq(split_name)
            ]

            split_rate = float(
                subset[
                    self.TARGET_COLUMN
                ].mean()
            )

            # This should normally be much tighter because sklearn
            # stratifies exactly by class counts. 2 percentage points
            # provides safe tolerance for small datasets.
            if abs(
                split_rate
                - overall_rate
            ) > 0.02:
                raise ValueError(
                    f"{split_name} target rate differs too much "
                    "from overall target rate."
                )

        # ----------------------------------------------------
        # Target-state consistency
        # ----------------------------------------------------

        invalid_churn = (
            data[
                self.TARGET_COLUMN
            ].eq(1)
            & data[
                "active_subscription_count_at_cutoff"
            ].gt(0)
        )

        if invalid_churn.any():
            raise ValueError(
                "Churned customer has active subscription "
                "at observation cutoff."
            )

        invalid_active = (
            data[
                self.TARGET_COLUMN
            ].eq(0)
            & data[
                "active_subscription_count_at_cutoff"
            ].eq(0)
        )

        if invalid_active.any():
            raise ValueError(
                "Non-churned customer has no active "
                "subscription at observation cutoff."
            )

        # ----------------------------------------------------
        # Target metadata percentages
        # ----------------------------------------------------

        percentage_columns = [
            "active_subscription_pct_at_cutoff",
            "expired_subscription_pct_at_cutoff",
            "active_contract_value_pct_at_cutoff",
            "expired_contract_value_pct_at_cutoff",
        ]

        for column in percentage_columns:

            if column not in data.columns:
                raise ValueError(
                    f"Training dataset is missing {column}."
                )

            invalid = (
                data[column].lt(0)
                | data[column].gt(100)
            )

            if invalid.any():
                raise ValueError(
                    f"{column} contains values outside 0-100."
                )

    # ========================================================
    # CONVENIENCE SPLITTER
    # ========================================================

    @staticmethod
    def split(
        bundle: TrainingDatasetBundle,
    ) -> dict[
        str,
        tuple[pd.DataFrame, pd.Series],
    ]:
        """
        Return model matrices:

        {
            "train": (X_train, y_train),
            "validation": (X_validation, y_validation),
            "test": (X_test, y_test),
        }
        """

        output: dict[
            str,
            tuple[pd.DataFrame, pd.Series],
        ] = {}

        for split_name in (
            "train",
            "validation",
            "test",
        ):

            subset = bundle.data.loc[
                bundle.data[
                    bundle.split_column
                ].eq(split_name)
            ].copy()

            x = subset[
                bundle.feature_columns
            ].copy()

            y = subset[
                bundle.target_column
            ].copy()

            output[
                split_name
            ] = (
                x,
                y,
            )

        return output