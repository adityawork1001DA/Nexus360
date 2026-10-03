from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from .common import utc_timestamp
from .feature_engineering import FeatureEngineer


class RevenueForecaster:

    FEATURES = [
        "time_index",
        "month_number",
        "quarter",
        "lag_1",
        "lag_2",
        "lag_3",
        "rolling_mean_3",
        "rolling_mean_6",
    ]

    def __init__(
        self,
        random_state: int = 42,
    ) -> None:
        self.random_state = random_state
        self.model: RandomForestRegressor | None = None
        self.metrics: dict = {}
        self.history: pd.DataFrame | None = None

    def train(
        self,
        df: pd.DataFrame,
    ) -> dict:

        prepared = (
            FeatureEngineer.forecasting_dataset(df)
        )

        model_data = prepared.dropna(
            subset=self.FEATURES
            + ["net_revenue_usd"]
        ).copy()

        if len(model_data) < 12:
            raise ValueError(
                "At least 12 usable monthly observations "
                "are required for forecasting."
            )

        test_size = max(
            3,
            int(round(len(model_data) * 0.20)),
        )

        if test_size >= len(model_data):
            test_size = max(
                1,
                len(model_data) // 4,
            )

        train = model_data.iloc[
            :-test_size
        ].copy()

        test = model_data.iloc[
            -test_size:
        ].copy()

        self.model = RandomForestRegressor(
            n_estimators=400,
            max_depth=10,
            min_samples_leaf=1,
            random_state=self.random_state,
            n_jobs=-1,
        )

        self.model.fit(
            train[self.FEATURES],
            train["net_revenue_usd"],
        )

        prediction = self.model.predict(
            test[self.FEATURES]
        )

        actual = test[
            "net_revenue_usd"
        ].to_numpy()

        mae = mean_absolute_error(
            actual,
            prediction,
        )

        rmse = np.sqrt(
            mean_squared_error(
                actual,
                prediction,
            )
        )

        nonzero = actual != 0

        mape = (
            float(
                np.mean(
                    np.abs(
                        (
                            actual[nonzero]
                            - prediction[nonzero]
                        )
                        / actual[nonzero]
                    )
                )
                * 100
            )
            if nonzero.any()
            else None
        )

        self.history = prepared[
            [
                "revenue_month",
                "net_revenue_usd",
            ]
        ].copy()

        self.metrics = {
            "model_type": "monthly_revenue_forecaster",
            "trained_at_utc": utc_timestamp(),
            "observations": int(len(model_data)),
            "train_observations": int(len(train)),
            "test_observations": int(len(test)),
            "mae": float(mae),
            "rmse": float(rmse),
            "mape_pct": mape,
            "r2": (
                float(
                    r2_score(
                        actual,
                        prediction,
                    )
                )
                if len(test) >= 2
                else None
            ),
        }

        return self.metrics

    def forecast(
        self,
        periods: int = 6,
    ) -> pd.DataFrame:

        if self.model is None or self.history is None:
            raise RuntimeError(
                "Forecaster must be trained first."
            )

        history = (
            self.history
            .sort_values("revenue_month")
            .reset_index(drop=True)
            .copy()
        )

        rows: list[dict] = []

        for _ in range(periods):

            revenue = history[
                "net_revenue_usd"
            ].astype(float)

            next_month = (
                history[
                    "revenue_month"
                ].max()
                + pd.offsets.MonthBegin(1)
            )

            features = pd.DataFrame(
                [
                    {
                        "time_index": len(history),
                        "month_number": next_month.month,
                        "quarter": next_month.quarter,
                        "lag_1": revenue.iloc[-1],
                        "lag_2": revenue.iloc[-2],
                        "lag_3": revenue.iloc[-3],
                        "rolling_mean_3": (
                            revenue.iloc[-3:].mean()
                        ),
                        "rolling_mean_6": (
                            revenue.iloc[-6:].mean()
                        ),
                    }
                ]
            )

            prediction = float(
                self.model.predict(
                    features[self.FEATURES]
                )[0]
            )

            prediction = max(
                0.0,
                prediction,
            )

            rows.append(
                {
                    "forecast_month": next_month,
                    "forecast_revenue_usd": prediction,
                }
            )

            history = pd.concat(
                [
                    history,
                    pd.DataFrame(
                        [
                            {
                                "revenue_month": next_month,
                                "net_revenue_usd": prediction,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            )

        return pd.DataFrame(rows)

    def save(
        self,
        path: str | Path,
    ) -> Path:

        if self.model is None:
            raise RuntimeError(
                "No trained model available."
            )

        output = Path(path)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            {
                "model": self.model,
                "history": self.history,
                "features": self.FEATURES,
            },
            output,
        )

        return output