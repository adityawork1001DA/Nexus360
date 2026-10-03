from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .common import utc_timestamp


class RevenueAnomalyDetector:

    FEATURES = [
        "daily_revenue",
        "transactions",
    ]

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
    ) -> None:
        self.contamination = contamination
        self.random_state = random_state
        self.model: IsolationForest | None = None
        self.metrics: dict = {}

    def fit_predict(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        data = df.copy()

        data["full_date"] = pd.to_datetime(
            data["full_date"],
            errors="coerce",
        )

        for column in self.FEATURES:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

        clean = data.dropna(
            subset=self.FEATURES
        ).copy()

        if len(clean) < 20:
            raise ValueError(
                "At least 20 observations are required "
                "for Isolation Forest anomaly detection."
            )

        self.model = IsolationForest(
            n_estimators=300,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )

        labels = self.model.fit_predict(
            clean[self.FEATURES]
        )

        scores = self.model.decision_function(
            clean[self.FEATURES]
        )

        clean[
            "ml_anomaly_flag"
        ] = (labels == -1).astype(int)

        clean[
            "ml_anomaly_score"
        ] = -scores

        sql_status = (
            clean["anomaly_status"]
            .fillna("")
            .astype(str)
            .str.lower()
        )

        clean[
            "sql_anomaly_flag"
        ] = (
            ~sql_status.isin(
                {
                    "",
                    "normal",
                    "none",
                    "no anomaly",
                }
            )
        ).astype(int)

        clean[
            "anomaly_agreement"
        ] = (
            clean["ml_anomaly_flag"]
            == clean["sql_anomaly_flag"]
        )

        self.metrics = {
            "model_type": "isolation_forest_revenue_anomaly",
            "trained_at_utc": utc_timestamp(),
            "rows": int(len(clean)),
            "ml_anomalies": int(
                clean["ml_anomaly_flag"].sum()
            ),
            "sql_anomalies": int(
                clean["sql_anomaly_flag"].sum()
            ),
            "agreement_pct": float(
                clean[
                    "anomaly_agreement"
                ].mean()
                * 100
            ),
        }

        return clean

    def save(
        self,
        path: str | Path,
    ) -> Path:

        if self.model is None:
            raise RuntimeError(
                "No trained anomaly model available."
            )

        output = Path(path)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        joblib.dump(
            self.model,
            output,
        )

        return output