from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine
from src.ml.historical_customer_features import (
    HistoricalCustomerFeatureBuilder,
)


@dataclass
class CurrentFeatureBundle:
    features: pd.DataFrame
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    scoring_cutoff: pd.Timestamp


class CurrentCustomerFeatureBuilder:
    """
    Build the latest available customer feature snapshot using the exact
    same point-in-time feature definitions used during historical training.
    """

    def __init__(
        self,
        scoring_cutoff: str | pd.Timestamp | None = None,
    ) -> None:
        self.engine = get_engine()

        if scoring_cutoff is None:
            self.scoring_cutoff = self._latest_available_date()
        else:
            self.scoring_cutoff = pd.Timestamp(
                scoring_cutoff
            ).normalize()

    def _latest_available_date(self) -> pd.Timestamp:
        """
        Determine the latest date for which warehouse business activity
        exists.

        Subscription end dates are intentionally NOT used because contracts
        may extend years into the future.
        """

        query = text(
            """
            WITH activity_dates AS (

                SELECT MAX(d.full_date) AS activity_date
                FROM warehouse.fact_revenue f
                JOIN warehouse.dim_date d
                  ON d.date_key = f.date_key

                UNION ALL

                SELECT MAX(d.full_date) AS activity_date
                FROM warehouse.fact_cloud_usage f
                JOIN warehouse.dim_date d
                  ON d.date_key = f.date_key

                UNION ALL

                SELECT MAX(d.full_date) AS activity_date
                FROM warehouse.fact_support_ticket f
                JOIN warehouse.dim_date d
                  ON d.date_key = f.opened_date_key

                UNION ALL

                SELECT MAX(d.full_date) AS activity_date
                FROM warehouse.fact_subscription f
                JOIN warehouse.dim_date d
                  ON d.date_key = f.start_date_key
            )

            SELECT MAX(activity_date) AS latest_available_date
            FROM activity_dates
            """
        )

        with self.engine.connect() as connection:
            result = pd.read_sql_query(
                query,
                connection,
            )

        if result.empty:
            raise ValueError(
                "Could not determine latest warehouse activity date."
            )

        value = result.loc[
            0,
            "latest_available_date",
        ]

        if isinstance(value, bytes):
            value = value.decode("utf-8")

        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(
                "Warehouse contains no usable activity dates."
            )

        if pd.isna(value):
            raise ValueError(
                "Warehouse contains no usable activity dates."
            )

        value = pd.Timestamp(str(value))
        return value.normalize()

    def build(self) -> CurrentFeatureBundle:
        historical_builder = HistoricalCustomerFeatureBuilder(
            observation_cutoff=self.scoring_cutoff
        )

        bundle = historical_builder.build()

        features = bundle.features.copy()

        if features.empty:
            raise ValueError(
                "Current customer feature snapshot is empty."
            )

        if features["customer_id"].duplicated().any():
            raise ValueError(
                "Current feature snapshot contains duplicate customers."
            )

        return CurrentFeatureBundle(
            features=features.reset_index(drop=True),
            feature_columns=list(bundle.feature_columns),
            numeric_features=list(bundle.numeric_features),
            categorical_features=list(bundle.categorical_features),
            scoring_cutoff=self.scoring_cutoff,
        )