from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


@dataclass
class HistoricalFeatureBundle:
    features: pd.DataFrame
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    observation_cutoff: pd.Timestamp
    window_start: pd.Timestamp


class HistoricalCustomerFeatureBuilder:
    """
    Leakage-safe point-in-time customer feature builder.

    Design
    ------
    Activity features:
        trailing 12 months ending at observation_cutoff

    Subscription features:
        information knowable at observation_cutoff

    Customer attributes:
        dimension values available for the customer

    The same builder is reused for historical training snapshots and
    current production scoring to prevent training-serving skew.
    """

    DEFAULT_CUTOFF = pd.Timestamp("2024-12-31")
    LOOKBACK_MONTHS = 12

    CATEGORICAL_FEATURES = [
        "industry",
        "customer_segment",
        "employee_band",
        "annual_revenue_band",
        "acquisition_channel",
        "customer_status",
        "is_ai_customer",
    ]

    def __init__(
        self,
        observation_cutoff: str | date | pd.Timestamp | None = None,
        lookback_months: int = LOOKBACK_MONTHS,
    ) -> None:
        self.engine = get_engine()

        self.observation_cutoff = pd.Timestamp(
            observation_cutoff or self.DEFAULT_CUTOFF
        ).normalize()

        if (
            not isinstance(lookback_months, int)
            or lookback_months <= 0
        ):
            raise ValueError(
                "lookback_months must be a positive integer."
            )

        self.lookback_months = lookback_months

        # Example:
        # cutoff       = 2024-12-31
        # window_start = 2024-01-01
        self.window_start = (
            self.observation_cutoff
            - pd.DateOffset(months=lookback_months)
            + pd.Timedelta(days=1)
        ).normalize()

    def _query(
        self,
        sql: str,
        params: dict | None = None,
    ) -> pd.DataFrame:
        with self.engine.connect() as connection:
            return pd.read_sql_query(
                text(sql),
                connection,
                params=params or {},
            )

    def _window_params(self) -> dict:
        return {
            "window_start": self.window_start.date(),
            "cutoff": self.observation_cutoff.date(),
        }

    def _load_customers(self) -> pd.DataFrame:
        return self._query(
            """
            SELECT
                c.customer_key,
                c.customer_id,
                c.customer_name,
                c.industry,
                c.customer_segment,
                c.employee_band,
                c.annual_revenue_band,
                c.acquisition_channel,
                c.signup_date,
                c.customer_status,
                c.is_ai_customer
            FROM warehouse.dim_customer c
            WHERE c.signup_date <= :cutoff
            """,
            {
                "cutoff": self.observation_cutoff.date(),
            },
        )

    def _load_revenue(self) -> pd.DataFrame:
        """
        Revenue behavior from only the trailing observation window.
        """

        return self._query(
            """
            SELECT
                f.customer_key,

                SUM(f.net_revenue_usd)
                    AS trailing_revenue_usd,

                SUM(f.gross_profit_usd)
                    AS trailing_gross_profit_usd,

                SUM(f.estimated_cost_usd)
                    AS trailing_revenue_cost_usd,

                COUNT(*)
                    AS trailing_transactions,

                COUNT(DISTINCT f.product_key)
                    AS trailing_products_purchased,

                MAX(d.full_date)
                    AS last_purchase_date

            FROM warehouse.fact_revenue f

            JOIN warehouse.dim_date d
              ON d.date_key = f.date_key

            WHERE d.full_date BETWEEN
                  :window_start AND :cutoff

            GROUP BY f.customer_key
            """,
            self._window_params(),
        )

    def _load_usage(self) -> pd.DataFrame:
        """
        Cloud/product consumption from trailing observation window.
        """

        return self._query(
            """
            SELECT
                f.customer_key,

                SUM(f.compute_hours)
                    AS trailing_compute_hours,

                SUM(f.storage_gb)
                    AS trailing_storage_gb,

                SUM(f.network_gb)
                    AS trailing_network_gb,

                SUM(f.ai_tokens_million)
                    AS trailing_ai_tokens_million,

                SUM(f.requests_count)
                    AS trailing_requests_count,

                SUM(f.failed_requests)
                    AS trailing_failed_requests,

                SUM(f.estimated_cost_usd)
                    AS trailing_cloud_cost_usd,

                SUM(f.carbon_estimate_kg)
                    AS trailing_carbon_kg

            FROM warehouse.fact_cloud_usage f

            JOIN warehouse.dim_date d
              ON d.date_key = f.date_key

            WHERE d.full_date BETWEEN
                  :window_start AND :cutoff

            GROUP BY f.customer_key
            """,
            self._window_params(),
        )

    def _load_support(self) -> pd.DataFrame:
        """
        Support experience from trailing observation window.
        """

        return self._query(
            """
            SELECT
                f.customer_key,

                COUNT(*)
                    AS trailing_support_tickets,

                COUNT(*) FILTER (
                    WHERE f.sla_met = FALSE
                ) AS trailing_sla_breaches,

                COUNT(*) FILTER (
                    WHERE f.reopened = TRUE
                ) AS trailing_reopened_tickets,

                AVG(f.resolution_hours)
                    AS trailing_avg_resolution_hours,

                AVG(f.customer_satisfaction)
                    AS trailing_avg_customer_satisfaction

            FROM warehouse.fact_support_ticket f

            JOIN warehouse.dim_date d
              ON d.date_key = f.opened_date_key

            WHERE d.full_date BETWEEN
                  :window_start AND :cutoff

            GROUP BY f.customer_key
            """,
            self._window_params(),
        )

    def _load_subscriptions(self) -> pd.DataFrame:
        """
        Subscription features available at the cutoff.

        In-force definition:
            start_date <= cutoff
            AND end_date > cutoff

        Historical subscription behavior is allowed only up to cutoff.
        Future subscription starts are never included.
        """

        return self._query(
            """
            SELECT
                f.customer_key,

                COUNT(*) FILTER (
                    WHERE ds.full_date <= :cutoff
                ) AS historical_subscription_count,

                COUNT(*) FILTER (
                    WHERE ds.full_date <= :cutoff
                      AND de.full_date > :cutoff
                ) AS subscriptions_in_force_at_cutoff,

                COALESCE(
                    SUM(
                        CASE
                            WHEN ds.full_date <= :cutoff
                             AND de.full_date > :cutoff
                            THEN f.contract_value_usd
                            ELSE 0
                        END
                    ),
                    0
                ) AS contract_value_in_force_at_cutoff,

                COUNT(*) FILTER (
                    WHERE ds.full_date <= :cutoff
                      AND de.full_date <= :cutoff
                ) AS subscriptions_expired_by_cutoff,

                COUNT(*) FILTER (
                    WHERE ds.full_date <= :cutoff
                      AND f.auto_renew = TRUE
                ) AS historical_auto_renew_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN ds.full_date <= :cutoff
                            THEN f.contract_value_usd
                            ELSE 0
                        END
                    ),
                    0
                ) AS historical_contract_value_usd,

                MIN(ds.full_date) FILTER (
                    WHERE ds.full_date <= :cutoff
                ) AS first_subscription_date,

                MAX(ds.full_date) FILTER (
                    WHERE ds.full_date <= :cutoff
                ) AS latest_subscription_start_date

            FROM warehouse.fact_subscription f

            JOIN warehouse.dim_date ds
              ON ds.date_key = f.start_date_key

            JOIN warehouse.dim_date de
              ON de.date_key = f.end_date_key

            GROUP BY f.customer_key
            """,
            {
                "cutoff": self.observation_cutoff.date(),
            },
        )

    @staticmethod
    def _safe_divide(
        numerator: pd.Series,
        denominator: pd.Series,
        multiplier: float = 1.0,
    ) -> pd.Series:

        numerator = pd.to_numeric(
            numerator,
            errors="coerce",
        ).fillna(0.0)

        denominator = pd.to_numeric(
            denominator,
            errors="coerce",
        ).fillna(0.0)

        values = np.where(
            denominator > 0,
            numerator / denominator * multiplier,
            0.0,
        )

        return pd.Series(
            values,
            index=numerator.index,
            dtype=float,
        )

    def build(self) -> HistoricalFeatureBundle:
        customers = self._load_customers()

        data = customers.copy()

        for frame in [
            self._load_revenue(),
            self._load_usage(),
            self._load_support(),
            self._load_subscriptions(),
        ]:
            data = data.merge(
                frame,
                on="customer_key",
                how="left",
                validate="one_to_one",
            )

        zero_columns = [
            "trailing_revenue_usd",
            "trailing_gross_profit_usd",
            "trailing_revenue_cost_usd",
            "trailing_transactions",
            "trailing_products_purchased",
            "trailing_compute_hours",
            "trailing_storage_gb",
            "trailing_network_gb",
            "trailing_ai_tokens_million",
            "trailing_requests_count",
            "trailing_failed_requests",
            "trailing_cloud_cost_usd",
            "trailing_carbon_kg",
            "trailing_support_tickets",
            "trailing_sla_breaches",
            "trailing_reopened_tickets",
            "trailing_avg_resolution_hours",
            "trailing_avg_customer_satisfaction",
            "historical_subscription_count",
            "subscriptions_in_force_at_cutoff",
            "contract_value_in_force_at_cutoff",
            "subscriptions_expired_by_cutoff",
            "historical_auto_renew_count",
            "historical_contract_value_usd",
        ]

        for column in zero_columns:
            if column in data.columns:
                data[column] = pd.to_numeric(
                    data[column],
                    errors="coerce",
                ).fillna(0.0)

        date_columns = [
            "signup_date",
            "last_purchase_date",
            "first_subscription_date",
            "latest_subscription_start_date",
        ]

        for column in date_columns:
            if column in data.columns:
                data[column] = pd.to_datetime(
                    data[column],
                    errors="coerce",
                )

        # Raw tenure retained for reporting.
        raw_tenure = (
            self.observation_cutoff
            - data["signup_date"]
        ).dt.days.fillna(0).clip(lower=0)

        data[
            "customer_tenure_days_at_cutoff"
        ] = raw_tenure

        # Model-friendly tenure transformation.
        data[
            "log_customer_tenure_days"
        ] = np.log1p(
            raw_tenure.astype(float)
        )

        days_since_purchase = (
            self.observation_cutoff
            - data["last_purchase_date"]
        ).dt.days

        # If no purchase exists in the trailing window, use the
        # window length + 1 rather than lifetime tenure.
        window_days = (
            self.observation_cutoff
            - self.window_start
        ).days + 1

        data[
            "days_since_last_purchase"
        ] = (
            days_since_purchase
            .fillna(window_days + 1)
            .clip(
                lower=0,
                upper=window_days + 1,
            )
        )

        data[
            "trailing_gross_margin_pct"
        ] = self._safe_divide(
            data["trailing_gross_profit_usd"],
            data["trailing_revenue_usd"],
            100.0,
        )

        data[
            "trailing_request_failure_rate_pct"
        ] = self._safe_divide(
            data["trailing_failed_requests"],
            data["trailing_requests_count"],
            100.0,
        )

        data[
            "trailing_sla_breach_rate_pct"
        ] = self._safe_divide(
            data["trailing_sla_breaches"],
            data["trailing_support_tickets"],
            100.0,
        )

        data[
            "trailing_reopen_rate_pct"
        ] = self._safe_divide(
            data["trailing_reopened_tickets"],
            data["trailing_support_tickets"],
            100.0,
        )

        data[
            "trailing_revenue_per_transaction"
        ] = self._safe_divide(
            data["trailing_revenue_usd"],
            data["trailing_transactions"],
        )

        data[
            "trailing_revenue_per_product"
        ] = self._safe_divide(
            data["trailing_revenue_usd"],
            data["trailing_products_purchased"],
        )

        data[
            "trailing_cloud_cost_to_revenue_pct"
        ] = self._safe_divide(
            data["trailing_cloud_cost_usd"],
            data["trailing_revenue_usd"],
            100.0,
        )

        data[
            "historical_auto_renew_pct"
        ] = self._safe_divide(
            data["historical_auto_renew_count"],
            data["historical_subscription_count"],
            100.0,
        )

        # Customer must have at least one subscription in force at
        # observation time. Otherwise churn prediction has no sensible
        # renewal interpretation.
        data = data.loc[
            data[
                "subscriptions_in_force_at_cutoff"
            ] > 0
        ].copy()

        if data.empty:
            raise ValueError(
                "No customers are eligible at the observation cutoff."
            )

        if data["customer_id"].duplicated().any():
            raise ValueError(
                "Feature dataset contains duplicate customers."
            )

        categorical_features = [
            column
            for column in self.CATEGORICAL_FEATURES
            if column in data.columns
        ]

        # Raw tenure is intentionally excluded from model input.
        # log_customer_tenure_days is used instead.
        excluded = {
            "customer_key",
            "customer_id",
            "customer_name",
            "signup_date",
            "last_purchase_date",
            "first_subscription_date",
            "latest_subscription_start_date",
            "customer_tenure_days_at_cutoff",
        }

        feature_columns = [
            column
            for column in data.columns
            if column not in excluded
        ]

        numeric_features = [
            column
            for column in feature_columns
            if column not in categorical_features
        ]

        invalid_numeric = []

        for column in numeric_features:
            values = pd.to_numeric(
                data[column],
                errors="coerce",
            )

            if not np.isfinite(
                values.fillna(0.0)
            ).all():
                invalid_numeric.append(column)

        if invalid_numeric:
            raise ValueError(
                "Non-finite numeric features detected: "
                f"{invalid_numeric}"
            )

        return HistoricalFeatureBundle(
            features=data.reset_index(drop=True),
            feature_columns=feature_columns,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            observation_cutoff=self.observation_cutoff,
            window_start=self.window_start,
        )