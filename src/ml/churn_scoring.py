from __future__ import annotations

import numpy as np
import pandas as pd

from src.ml.churn_model import ChurnModelBundle


class CustomerChurnScorer:

    def __init__(
        self,
        model_bundle: ChurnModelBundle,
    ) -> None:
        self.bundle = model_bundle

    def _risk_band(
        self,
        probability: float,
    ) -> str:
        """
        Business risk bands aligned with the model's
        validated decision threshold.

        Critical:
            At or above the production churn threshold.

        High / Medium:
            Elevated risk below the classification threshold.

        Low:
            Relatively low predicted churn risk.
        """

        threshold = float(self.bundle.threshold)

        if probability >= threshold:
            return "Critical"

        if probability >= threshold * 0.625:
            return "High"

        if probability >= threshold * 0.25:
            return "Medium"

        return "Low"

    def score(
        self,
        data: pd.DataFrame | None = None,
    ) -> pd.DataFrame:

        if data is None:
            data = self.bundle.training_data.copy()
        else:
            data = data.copy()

        missing = [
            column
            for column in self.bundle.feature_columns
            if column not in data.columns
        ]

        if missing:
            raise ValueError(
                "Scoring dataset is missing model features: "
                f"{missing}"
            )

        X = data[
            self.bundle.feature_columns
        ]

        probabilities = (
            self.bundle.pipeline.predict_proba(X)[:, 1]
        )

        predictions = (
            probabilities
            >= self.bundle.threshold
        ).astype(int)

        identity_columns = [
            column
            for column in [
                "customer_id",
                "customer_name",
                "customer_segment",
                "industry",
                "historical_revenue_usd",
                "contract_value_in_force_at_cutoff",
                "dataset_split",
                "churn_target",
                "future_subscription_state",
            ]
            if column in data.columns
        ]

        result = data[
            identity_columns
        ].copy()

        result[
            "churn_probability"
        ] = probabilities

        result[
            "churn_probability_pct"
        ] = (
            probabilities * 100
        ).round(2)

        result[
            "churn_prediction"
        ] = predictions

        result["risk_band"] = [
            self._risk_band(probability)
            for probability in probabilities
        ]

        if (
            "historical_revenue_usd"
            in result.columns
        ):
            result[
                "model_revenue_at_risk_usd"
            ] = (
                result[
                    "historical_revenue_usd"
                ]
                .fillna(0)
                .clip(lower=0)
                * result["churn_probability"]
            ).round(2)

        result["risk_rank"] = (
            pd.Series(
                probabilities,
                index=result.index,
            )
            .rank(
                method="first",
                ascending=False,
            )
            .astype(int)
        )

        result[
            "observation_cutoff"
        ] = self.bundle.observation_cutoff

        result[
            "prediction_end"
        ] = self.bundle.prediction_end

        result = result.sort_values(
            [
                "churn_probability",
                "risk_rank",
            ],
            ascending=[
                False,
                True,
            ],
        ).reset_index(drop=True)

        if not np.isfinite(
            result["churn_probability"]
        ).all():
            raise ValueError(
                "Non-finite churn probabilities generated."
            )

        return result