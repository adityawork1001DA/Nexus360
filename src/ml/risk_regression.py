from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .common import utc_timestamp
from .feature_engineering import FeatureEngineer


class RevenueRiskRegressor:

    def __init__(
        self,
        random_state: int = 42,
    ) -> None:
        self.random_state = random_state
        self.pipeline: Pipeline | None = None
        self.metrics: dict = {}

    def _build_pipeline(self) -> Pipeline:

        numeric = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="median"),
                ),
            ]
        )

        categorical = Pipeline(
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

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    numeric,
                    FeatureEngineer.RISK_NUMERIC,
                ),
                (
                    "categorical",
                    categorical,
                    FeatureEngineer.RISK_CATEGORICAL,
                ),
            ]
        )

        model = RandomForestRegressor(
            n_estimators=400,
            max_depth=14,
            min_samples_leaf=2,
            random_state=self.random_state,
            n_jobs=-1,
        )

        return Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor,
                ),
                (
                    "model",
                    model,
                ),
            ]
        )

    def train(
        self,
        df: pd.DataFrame,
    ) -> dict:

        X, y, _ = (
            FeatureEngineer.revenue_risk_dataset(df)
        )

        X_train, X_test, y_train, y_test = (
            train_test_split(
                X,
                y,
                test_size=0.25,
                random_state=self.random_state,
            )
        )

        self.pipeline = self._build_pipeline()

        self.pipeline.fit(
            X_train,
            y_train,
        )

        prediction = self.pipeline.predict(
            X_test
        )

        mae = mean_absolute_error(
            y_test,
            prediction,
        )

        rmse = np.sqrt(
            mean_squared_error(
                y_test,
                prediction,
            )
        )

        self.metrics = {
            "model_type": "revenue_at_risk_regressor",
            "trained_at_utc": utc_timestamp(),
            "rows": int(len(df)),
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(
                r2_score(
                    y_test,
                    prediction,
                )
            ),
        }

        return self.metrics

    def predict(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        if self.pipeline is None:
            raise RuntimeError(
                "Model must be trained before prediction."
            )

        X, actual, identifiers = (
            FeatureEngineer.revenue_risk_dataset(df)
        )

        predicted = self.pipeline.predict(X)

        result = identifiers.copy()

        result["actual_revenue_at_risk_usd"] = (
            actual.to_numpy()
        )

        result["predicted_revenue_at_risk_usd"] = (
            np.maximum(
                predicted,
                0,
            )
        )

        result["absolute_error_usd"] = np.abs(
            result[
                "actual_revenue_at_risk_usd"
            ]
            - result[
                "predicted_revenue_at_risk_usd"
            ]
        )

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