from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.ml.historical_training_dataset import (
    HistoricalCustomerTrainingDatasetBuilder,
)


RANDOM_STATE = 42


@dataclass
class ModelEvaluation:
    model_name: str
    threshold: float
    roc_auc: float
    pr_auc: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    tn: int
    fp: int
    fn: int
    tp: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "threshold": self.threshold,
            "roc_auc": self.roc_auc,
            "pr_auc": self.pr_auc,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "tn": self.tn,
            "fp": self.fp,
            "fn": self.fn,
            "tp": self.tp,
        }


@dataclass
class ChurnModelBundle:
    pipeline: Pipeline
    model_name: str
    threshold: float

    validation_metrics: ModelEvaluation
    test_metrics: ModelEvaluation

    candidate_metrics: list[dict[str, Any]]

    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]

    training_data: pd.DataFrame

    observation_cutoff: pd.Timestamp
    prediction_end: pd.Timestamp


class ChurnModelTrainer:
    """
    Leakage-safe historical churn model.

    Model selection:
        validation PR-AUC
        -> validation ROC-AUC
        -> validation F1

    Test data is never used for model or threshold selection.
    """

    def __init__(
        self,
        dataset_builder: HistoricalCustomerTrainingDatasetBuilder | None = None,
        random_state: int = RANDOM_STATE,
    ) -> None:

        self.dataset_builder = (
            dataset_builder
            or HistoricalCustomerTrainingDatasetBuilder()
        )

        self.random_state = random_state

    @staticmethod
    def _one_hot_encoder() -> OneHotEncoder:
        try:
            return OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            )
        except TypeError:
            return OneHotEncoder(
                handle_unknown="ignore",
                sparse=False,
            )

    def _preprocessor(
        self,
        numeric_features: list[str],
        categorical_features: list[str],
    ) -> ColumnTransformer:

        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="median"),
                ),
                (
                    "scaler",
                    StandardScaler(),
                ),
            ]
        )

        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="constant",
                        fill_value="Unknown",
                    ),
                ),
                (
                    "encoder",
                    self._one_hot_encoder(),
                ),
            ]
        )

        return ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    numeric_pipeline,
                    numeric_features,
                ),
                (
                    "categorical",
                    categorical_pipeline,
                    categorical_features,
                ),
            ],
            remainder="drop",
        )

    def _candidate_models(self) -> dict[str, Any]:
        return {
            "logistic_regression": LogisticRegression(
                max_iter=3000,
                class_weight="balanced",
                random_state=self.random_state,
            ),

            "random_forest": RandomForestClassifier(
                n_estimators=500,
                max_depth=10,
                min_samples_leaf=4,
                max_features="sqrt",
                class_weight="balanced",
                n_jobs=-1,
                random_state=self.random_state,
            ),

            "hist_gradient_boosting": HistGradientBoostingClassifier(
                learning_rate=0.05,
                max_iter=300,
                max_leaf_nodes=20,
                min_samples_leaf=20,
                l2_regularization=2.0,
                random_state=self.random_state,
            ),
        }

    @staticmethod
    def _evaluate(
        y_true,
        probabilities: np.ndarray,
        threshold: float,
        model_name: str,
    ) -> ModelEvaluation:

        probabilities = np.asarray(
            probabilities,
            dtype=float,
        )

        predictions = (
            probabilities >= threshold
        ).astype(int)

        tn, fp, fn, tp = confusion_matrix(
            y_true,
            predictions,
            labels=[0, 1],
        ).ravel()

        return ModelEvaluation(
            model_name=model_name,
            threshold=float(threshold),

            roc_auc=float(
                roc_auc_score(
                    y_true,
                    probabilities,
                )
            ),

            pr_auc=float(
                average_precision_score(
                    y_true,
                    probabilities,
                )
            ),

            accuracy=float(
                accuracy_score(
                    y_true,
                    predictions,
                )
            ),

            precision=float(
                precision_score(
                    y_true,
                    predictions,
                    zero_division=0,
                )
            ),

            recall=float(
                recall_score(
                    y_true,
                    predictions,
                    zero_division=0,
                )
            ),

            f1=float(
                f1_score(
                    y_true,
                    predictions,
                    zero_division=0,
                )
            ),

            tn=int(tn),
            fp=int(fp),
            fn=int(fn),
            tp=int(tp),
        )

    @staticmethod
    def _best_threshold(
        y_true,
        probabilities: np.ndarray,
    ) -> float:
        """
        Threshold selected only from validation data.

        With a ~6.5% positive class, optimizing F1 is more useful
        than blindly using 0.50.
        """

        best_threshold = 0.50
        best_f1 = -1.0
        best_recall = -1.0

        for threshold in np.arange(
            0.05,
            0.81,
            0.01,
        ):
            predictions = (
                probabilities >= threshold
            ).astype(int)

            current_f1 = f1_score(
                y_true,
                predictions,
                zero_division=0,
            )

            current_recall = recall_score(
                y_true,
                predictions,
                zero_division=0,
            )

            if (
                current_f1 > best_f1
                or (
                    np.isclose(current_f1, best_f1)
                    and current_recall > best_recall
                )
            ):
                best_f1 = current_f1
                best_recall = current_recall
                best_threshold = float(threshold)

        return round(best_threshold, 2)

    def build(self) -> ChurnModelBundle:

        dataset = self.dataset_builder.build()

        data = dataset.data.copy()

        feature_columns = list(
            dataset.feature_columns
        )

        numeric_features = list(
            dataset.numeric_features
        )

        categorical_features = list(
            dataset.categorical_features
        )

        train = data.loc[
            data["dataset_split"] == "train"
        ].copy()

        validation = data.loc[
            data["dataset_split"] == "validation"
        ].copy()

        test = data.loc[
            data["dataset_split"] == "test"
        ].copy()

        X_train = train[feature_columns]
        y_train = train["churn_target"].astype(int)

        X_validation = validation[feature_columns]
        y_validation = validation[
            "churn_target"
        ].astype(int)

        X_test = test[feature_columns]
        y_test = test["churn_target"].astype(int)

        for name, target in (
            ("train", y_train),
            ("validation", y_validation),
            ("test", y_test),
        ):
            if set(target.unique()) != {0, 1}:
                raise ValueError(
                    f"{name} split must contain both classes."
                )

        base_preprocessor = self._preprocessor(
            numeric_features=numeric_features,
            categorical_features=categorical_features,
        )

        results = []

        for model_name, estimator in (
            self._candidate_models().items()
        ):

            pipeline = Pipeline(
                steps=[
                    (
                        "preprocessor",
                        clone(base_preprocessor),
                    ),
                    (
                        "model",
                        estimator,
                    ),
                ]
            )

            pipeline.fit(
                X_train,
                y_train,
            )

            validation_probability = (
                pipeline.predict_proba(
                    X_validation
                )[:, 1]
            )

            threshold = self._best_threshold(
                y_validation,
                validation_probability,
            )

            validation_metrics = self._evaluate(
                y_true=y_validation,
                probabilities=validation_probability,
                threshold=threshold,
                model_name=model_name,
            )

            results.append(
                (
                    model_name,
                    pipeline,
                    threshold,
                    validation_metrics,
                )
            )

        # Imbalanced classification:
        # PR-AUC gets first priority.
        results.sort(
            key=lambda item: (
                item[3].pr_auc,
                item[3].roc_auc,
                item[3].f1,
            ),
            reverse=True,
        )

        (
            best_model_name,
            best_pipeline,
            best_threshold,
            best_validation_metrics,
        ) = results[0]

        # Test set is touched for the first time here.
        test_probability = (
            best_pipeline.predict_proba(
                X_test
            )[:, 1]
        )

        test_metrics = self._evaluate(
            y_true=y_test,
            probabilities=test_probability,
            threshold=best_threshold,
            model_name=best_model_name,
        )

        candidate_metrics = [
            item[3].to_dict()
            for item in results
        ]

        return ChurnModelBundle(
            pipeline=best_pipeline,
            model_name=best_model_name,
            threshold=best_threshold,
            validation_metrics=best_validation_metrics,
            test_metrics=test_metrics,
            candidate_metrics=candidate_metrics,
            feature_columns=feature_columns,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            training_data=data,
            observation_cutoff=dataset.observation_cutoff,
            prediction_end=dataset.prediction_end,
        )