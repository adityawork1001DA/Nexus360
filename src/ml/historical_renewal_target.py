from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


@dataclass
class HistoricalTargetBundle:
    targets: pd.DataFrame
    observation_cutoff: pd.Timestamp
    prediction_end: pd.Timestamp


class HistoricalRenewalTargetBuilder:

    DEFAULT_CUTOFF = pd.Timestamp("2024-12-31")
    DEFAULT_PREDICTION_END = pd.Timestamp("2025-12-31")

    def __init__(
        self,
        observation_cutoff: str | date | pd.Timestamp | None = None,
        prediction_end: str | date | pd.Timestamp | None = None,
    ) -> None:
        self.engine = get_engine()

        self.observation_cutoff = pd.Timestamp(
            observation_cutoff or self.DEFAULT_CUTOFF
        ).normalize()

        self.prediction_end = pd.Timestamp(
            prediction_end or self.DEFAULT_PREDICTION_END
        ).normalize()

        if self.prediction_end <= self.observation_cutoff:
            raise ValueError(
                "prediction_end must be after observation_cutoff."
            )

    def build(self) -> HistoricalTargetBundle:
        query = text(
            """
            WITH subscription_dates AS (
                SELECT
                    f.customer_key,
                    f.subscription_id,
                    ds.full_date AS start_date,
                    de.full_date AS end_date
                FROM warehouse.fact_subscription f
                JOIN warehouse.dim_date ds
                  ON ds.date_key = f.start_date_key
                JOIN warehouse.dim_date de
                  ON de.date_key = f.end_date_key
            ),

            eligible AS (
                SELECT DISTINCT customer_key
                FROM subscription_dates
                WHERE start_date <= :cutoff
                  AND end_date > :cutoff
            ),

            future_state AS (
                SELECT
                    e.customer_key,

                    COUNT(sd.subscription_id) FILTER (
                        WHERE sd.start_date <= :prediction_end
                          AND sd.end_date > :prediction_end
                    ) AS subscriptions_in_force_at_prediction_end,

                    COUNT(sd.subscription_id) FILTER (
                        WHERE sd.start_date > :cutoff
                          AND sd.start_date <= :prediction_end
                    ) AS subscriptions_started_during_followup

                FROM eligible e

                LEFT JOIN subscription_dates sd
                  ON sd.customer_key = e.customer_key

                GROUP BY e.customer_key
            )

            SELECT
                c.customer_id,
                fs.subscriptions_in_force_at_prediction_end,
                fs.subscriptions_started_during_followup,

                CASE
                    WHEN fs.subscriptions_in_force_at_prediction_end = 0
                    THEN 1
                    ELSE 0
                END AS churn_target,

                CASE
                    WHEN fs.subscriptions_in_force_at_prediction_end = 0
                    THEN 'Churned'
                    ELSE 'Retained'
                END AS future_subscription_state

            FROM future_state fs

            JOIN warehouse.dim_customer c
              ON c.customer_key = fs.customer_key

            ORDER BY c.customer_id
            """
        )

        with self.engine.connect() as connection:
            targets = pd.read_sql_query(
                query,
                connection,
                params={
                    "cutoff": self.observation_cutoff.date(),
                    "prediction_end": self.prediction_end.date(),
                },
            )

        if targets.empty:
            raise ValueError(
                "Historical target builder produced no observations."
            )

        if targets["customer_id"].duplicated().any():
            raise ValueError(
                "Historical target contains duplicate customers."
            )

        if targets["churn_target"].isna().any():
            raise ValueError(
                "Historical churn target contains null values."
            )

        targets["churn_target"] = (
            targets["churn_target"].astype(int)
        )

        classes = set(targets["churn_target"].unique())

        if classes != {0, 1}:
            raise ValueError(
                "Historical target requires both churned and retained "
                f"customers. Found classes: {sorted(classes)}"
            )

        return HistoricalTargetBundle(
            targets=targets,
            observation_cutoff=self.observation_cutoff,
            prediction_end=self.prediction_end,
        )