from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .common import utc_timestamp
from .feature_engineering import FeatureEngineer


class RenewalRiskModel:

    def __init__(
        self,
        random_state: int = 42,
    ) -> None:
        self.random_state = random_state
        self.pipeline: Pipeline | None = None
        self.metrics: dict = {}

    def _preprocessor(self) -> ColumnTransformer:

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
                        strategy="most_frequent"
                    ),
                ),
                (
                    "encoder",
                    OneHotEncoder(
                        handle_unknown="ignore"
                    ),
                ),
            ]
        )

        return ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    numeric_pipeline,
                    FeatureEngineer.RENEWAL_NUMERIC,
                ),
                (
                    "categorical",
                    categorical_pipeline,
                    FeatureEngineer.RENEWAL_CATEGORICAL,
                ),
            ]
        )

    def train(
        self,
        df: pd.DataFrame,
    ) -> dict:

        X, y, _ = FeatureEngineer.renewal_dataset(df)

        if y.nunique() < 2:
            raise ValueError(
                "Renewal target contains only one class. "
                "Classification requires both low-risk and high-risk examples."
            )

        stratify = y if y.value_counts().min() >= 2 else None

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=self.random_state,
            stratify=stratify,
        )

        candidates = {
            "logistic_regression": LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=self.random_state,
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=300,
                max_depth=12,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=self.random_state,
                n_jobs=-1,
            ),
        }

        comparison: dict[str, dict] = {}
        best_name = None
        best_score = -np.inf
        best_pipeline = None

        min_class = int(y_train.value_counts().min())

        cv_splits = min(
            5,
            min_class,
        )

        for name, estimator in candidates.items():

            pipeline = Pipeline(
                steps=[
                    (
                        "preprocessor",
                        self._preprocessor(),
                    ),
                    (
                        "model",
                        estimator,
                    ),
                ]
            )

            cv_auc = None

            if cv_splits >= 2:
                cv = StratifiedKFold(
                    n_splits=cv_splits,
                    shuffle=True,
                    random_state=self.random_state,
                )

                scores = cross_val_score(
                    pipeline,
                    X_train,
                    y_train,
                    cv=cv,
                    scoring="roc_auc",
                    n_jobs=-1,
                )

                cv_auc = float(scores.mean())

            pipeline.fit(
                X_train,
                y_train,
            )

            probabilities = pipeline.predict_proba(
                X_test
            )[:, 1]

            predictions = (
                probabilities >= 0.5
            ).astype(int)

            test_auc = (
                float(
                    roc_auc_score(
                        y_test,
                        probabilities,
                    )
                )
                if y_test.nunique() == 2
                else None
            )

            score = (
                cv_auc
                if cv_auc is not None
                else (
                    test_auc
                    if test_auc is not None
                    else f1_score(
                        y_test,
                        predictions,
                        zero_division=0,
                    )
                )
            )

            comparison[name] = {
                "cv_roc_auc": cv_auc,
                "test_roc_auc": test_auc,
                "test_f1": float(
                    f1_score(
                        y_test,
                        predictions,
                        zero_division=0,
                    )
                ),
            }

            if score > best_score:
                best_score = score
                best_name = name
                best_pipeline = pipeline

        if best_pipeline is None:
            raise RuntimeError(
                "No valid renewal model could be trained."
            )

        self.pipeline = best_pipeline

        probabilities = self.pipeline.predict_proba(
            X_test
        )[:, 1]

        predictions = (
            probabilities >= 0.5
        ).astype(int)

        self.metrics = {
            "model_type": "renewal_risk_classifier",
            "selected_model": best_name,
            "trained_at_utc": utc_timestamp(),
            "rows": int(len(df)),
            "positive_rate": float(y.mean()),
            "accuracy": float(
                accuracy_score(
                    y_test,
                    predictions,
                )
            ),
            "precision": float(
                precision_score(
                    y_test,
                    predictions,
                    zero_division=0,
                )
            ),
            "recall": float(
                recall_score(
                    y_test,
                    predictions,
                    zero_division=0,
                )
            ),
            "f1": float(
                f1_score(
                    y_test,
                    predictions,
                    zero_division=0,
                )
            ),
            "roc_auc": (
                float(
                    roc_auc_score(
                        y_test,
                        probabilities,
                    )
                )
                if y_test.nunique() == 2
                else None
            ),
            "confusion_matrix": (
                confusion_matrix(
                    y_test,
                    predictions,
                ).tolist()
            ),
            "classification_report": (
                classification_report(
                    y_test,
                    predictions,
                    output_dict=True,
                    zero_division=0,
                )
            ),
            "model_comparison": comparison,
        }

        return self.metrics

    def predict(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        if self.pipeline is None:
            raise RuntimeError(
                "Model must be trained or loaded before prediction."
            )

        X, actual, identifiers = (
            FeatureEngineer.renewal_dataset(df)
        )

        probability = self.pipeline.predict_proba(
            X
        )[:, 1]

        result = identifiers.copy()

        result["actual_risk_flag"] = (
            actual.to_numpy()
        )

        result["predicted_renewal_risk_probability"] = (
            probability
        )

        result["predicted_renewal_risk_flag"] = (
            probability >= 0.5
        ).astype(int)

        result["predicted_risk_band"] = pd.cut(
            probability,
            bins=[
                -np.inf,
                0.25,
                0.50,
                0.75,
                np.inf,
            ],
            labels=[
                "Low",
                "Medium",
                "High",
                "Critical",
            ],
        ).astype(str)

        return result

    def save(
        self,
        path: str | Path,
    ) -> Path:

        if self.pipeline is None:
            raise RuntimeError(
                "No trained model available."
            )

        output = Path(path)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            self.pipeline,
            output,
        )

        return output