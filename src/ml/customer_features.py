from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analytics.data_loader import AnalyticsDataLoader


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CustomerFeatureBundle:
    """
    Container for the customer-level machine-learning feature dataset.
    """

    features: pd.DataFrame
    feature_columns: list[str]
    numeric_features: list[str]
    categorical_features: list[str]
    identifier_columns: list[str]


class CustomerFeatureBuilder:
    """
    Build a customer-level ML feature table from the Nexus 360
    analytics semantic layer.

    Sources
    -------
    analytics.v_customer_360
    analytics.v_subscription_renewal_risk
    analytics.v_revenue_at_risk

    Important
    ---------
    This class builds predictive features only.

    It deliberately does NOT create a churn target yet. The target must
    be defined from an observable business outcome rather than from an
    existing risk score, otherwise target leakage would be introduced.
    """

    IDENTIFIER_COLUMNS = [
        "customer_id",
        "customer_name",
    ]

    NUMERIC_FEATURES = [
        # Commercial value
        "lifetime_revenue_usd",
        "lifetime_gross_profit_usd",
        "transactions",
        "purchased_products",

        # Subscription footprint
        "subscriptions",
        "active_subscriptions",
        "active_contract_value_usd",

        # Support experience
        "support_tickets",
        "sla_breaches",
        "reopened_tickets",
        "avg_resolution_hours",
        "avg_customer_satisfaction",

        # Cloud usage
        "compute_hours",
        "storage_gb",
        "network_gb",
        "ai_tokens_million",
        "requests_count",
        "failed_requests",
        "request_failure_rate_pct",
        "cloud_cost_usd",

        # Subscription risk aggregation
        "subscription_count_risk_view",
        "avg_renewal_risk_score",
        "max_renewal_risk_score",
        "high_risk_subscription_count",
        "critical_risk_subscription_count",
        "auto_renew_subscription_count",
        "auto_renew_subscription_pct",
        "subscription_contract_value_usd",

        # Revenue-risk / operational aggregation
        "composite_risk_score",
        "revenue_at_risk_usd",
        "risk_view_renewal_score",
        "risk_support_ticket_count",
        "risk_sla_compliance_pct",
        "risk_reopen_rate_pct",
        "risk_avg_resolution_hours",
        "risk_avg_customer_satisfaction",
        "risk_requests_count",
        "risk_failed_requests",
        "risk_request_failure_rate_pct",

        # Engineered ratios
        "gross_margin_pct",
        "revenue_per_transaction",
        "gross_profit_per_transaction",
        "revenue_per_product",
        "cloud_cost_to_revenue_pct",
        "support_tickets_per_transaction",
        "sla_breach_rate_pct",
        "ticket_reopen_rate_pct",
        "failed_request_rate_calculated_pct",
        "active_subscription_pct",
        "contract_value_per_active_subscription",
        "ai_intensity_per_million_requests",

        # Customer tenure
        "customer_tenure_days",
    ]

    CATEGORICAL_FEATURES = [
        "industry",
        "customer_segment",
        "employee_band",
        "annual_revenue_band",
        "acquisition_channel",
        "customer_status",
        "is_ai_customer",
        "revenue_risk_band",
    ]

    def __init__(
        self,
        loader: AnalyticsDataLoader | None = None,
    ) -> None:

        self.loader = loader or AnalyticsDataLoader()

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build(self) -> CustomerFeatureBundle:
        """
        Build and return the complete customer-level feature dataset.
        """

        logger.info(
            "Loading customer ML source datasets."
        )

        customer_360 = self.loader.load_view(
            "v_customer_360"
        )

        subscription_risk = self.loader.load_view(
            "v_subscription_renewal_risk"
        )

        revenue_risk = self.loader.load_view(
            "v_revenue_at_risk"
        )

        self._validate_sources(
            customer_360=customer_360,
            subscription_risk=subscription_risk,
            revenue_risk=revenue_risk,
        )

        logger.info(
            "Building subscription-level customer aggregates."
        )

        subscription_features = (
            self._build_subscription_features(
                subscription_risk
            )
        )

        logger.info(
            "Building revenue-risk customer features."
        )

        revenue_risk_features = (
            self._build_revenue_risk_features(
                revenue_risk
            )
        )

        logger.info(
            "Joining customer feature datasets."
        )

        features = (
            customer_360
            .merge(
                subscription_features,
                how="left",
                on="customer_id",
                validate="one_to_one",
            )
            .merge(
                revenue_risk_features,
                how="left",
                on="customer_id",
                validate="one_to_one",
            )
        )

        features = self._engineer_features(
            features
        )

        features = self._clean_features(
            features
        )

        self._validate_output(
            features
        )

        feature_columns = [
            *self.NUMERIC_FEATURES,
            *self.CATEGORICAL_FEATURES,
        ]

        logger.info(
            "Customer ML feature dataset built: %s rows, %s features.",
            len(features),
            len(feature_columns),
        )

        return CustomerFeatureBundle(
            features=features,
            feature_columns=feature_columns,
            numeric_features=list(
                self.NUMERIC_FEATURES
            ),
            categorical_features=list(
                self.CATEGORICAL_FEATURES
            ),
            identifier_columns=list(
                self.IDENTIFIER_COLUMNS
            ),
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _require_columns(
        dataframe: pd.DataFrame,
        required: set[str],
        dataset_name: str,
    ) -> None:

        missing = sorted(
            required
            - set(dataframe.columns)
        )

        if missing:
            raise ValueError(
                f"{dataset_name} is missing required columns: "
                + ", ".join(missing)
            )

    def _validate_sources(
        self,
        customer_360: pd.DataFrame,
        subscription_risk: pd.DataFrame,
        revenue_risk: pd.DataFrame,
    ) -> None:

        self._require_columns(
            customer_360,
            {
                "customer_id",
                "customer_name",
                "industry",
                "customer_segment",
                "employee_band",
                "annual_revenue_band",
                "acquisition_channel",
                "signup_date",
                "customer_status",
                "is_ai_customer",
                "lifetime_revenue_usd",
                "lifetime_gross_profit_usd",
                "transactions",
                "purchased_products",
                "subscriptions",
                "active_subscriptions",
                "active_contract_value_usd",
                "support_tickets",
                "sla_breaches",
                "reopened_tickets",
                "avg_resolution_hours",
                "avg_customer_satisfaction",
                "compute_hours",
                "storage_gb",
                "network_gb",
                "ai_tokens_million",
                "requests_count",
                "failed_requests",
                "request_failure_rate_pct",
                "cloud_cost_usd",
            },
            "v_customer_360",
        )

        self._require_columns(
            subscription_risk,
            {
                "subscription_id",
                "customer_id",
                "contract_value_usd",
                "auto_renew",
                "renewal_risk_score",
                "renewal_risk_band",
            },
            "v_subscription_renewal_risk",
        )

        self._require_columns(
            revenue_risk,
            {
                "customer_id",
                "renewal_risk_score",
                "support_ticket_count",
                "sla_compliance_pct",
                "reopen_rate_pct",
                "avg_resolution_hours",
                "avg_customer_satisfaction",
                "requests_count",
                "failed_requests",
                "request_failure_rate_pct",
                "composite_risk_score",
                "revenue_at_risk_usd",
                "revenue_risk_band",
            },
            "v_revenue_at_risk",
        )

        if customer_360.empty:
            raise ValueError(
                "v_customer_360 contains no rows."
            )

    # ========================================================
    # SUBSCRIPTION FEATURES
    # ========================================================

    @staticmethod
    def _risk_flag(
        series: pd.Series,
        keyword: str,
    ) -> pd.Series:

        return (
            series
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(
                keyword.lower(),
                regex=False,
            )
            .astype(int)
        )

    def _build_subscription_features(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if dataframe.empty:
            return pd.DataFrame(
                columns=[
                    "customer_id",
                    "subscription_count_risk_view",
                    "avg_renewal_risk_score",
                    "max_renewal_risk_score",
                    "high_risk_subscription_count",
                    "critical_risk_subscription_count",
                    "auto_renew_subscription_count",
                    "auto_renew_subscription_pct",
                    "subscription_contract_value_usd",
                ]
            )

        data = dataframe.copy()

        data["renewal_risk_score"] = (
            pd.to_numeric(
                data["renewal_risk_score"],
                errors="coerce",
            )
        )

        data["contract_value_usd"] = (
            pd.to_numeric(
                data["contract_value_usd"],
                errors="coerce",
            )
            .fillna(0.0)
        )

        data["auto_renew_flag"] = (
            data["auto_renew"]
            .fillna(False)
            .astype(bool)
            .astype(int)
        )

        data["high_risk_flag"] = (
            self._risk_flag(
                data["renewal_risk_band"],
                "high",
            )
        )

        data["critical_risk_flag"] = (
            self._risk_flag(
                data["renewal_risk_band"],
                "critical",
            )
        )

        grouped = (
            data
            .groupby(
                "customer_id",
                as_index=False,
            )
            .agg(
                subscription_count_risk_view=(
                    "subscription_id",
                    "nunique",
                ),
                avg_renewal_risk_score=(
                    "renewal_risk_score",
                    "mean",
                ),
                max_renewal_risk_score=(
                    "renewal_risk_score",
                    "max",
                ),
                high_risk_subscription_count=(
                    "high_risk_flag",
                    "sum",
                ),
                critical_risk_subscription_count=(
                    "critical_risk_flag",
                    "sum",
                ),
                auto_renew_subscription_count=(
                    "auto_renew_flag",
                    "sum",
                ),
                subscription_contract_value_usd=(
                    "contract_value_usd",
                    "sum",
                ),
            )
        )

        grouped[
            "auto_renew_subscription_pct"
        ] = np.where(
            grouped[
                "subscription_count_risk_view"
            ] > 0,
            (
                grouped[
                    "auto_renew_subscription_count"
                ]
                / grouped[
                    "subscription_count_risk_view"
                ]
                * 100
            ),
            0.0,
        )

        return grouped

    # ========================================================
    # REVENUE RISK FEATURES
    # ========================================================

    @staticmethod
    def _build_revenue_risk_features(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if dataframe.empty:
            return pd.DataFrame(
                columns=[
                    "customer_id",
                    "risk_view_renewal_score",
                    "risk_support_ticket_count",
                    "risk_sla_compliance_pct",
                    "risk_reopen_rate_pct",
                    "risk_avg_resolution_hours",
                    "risk_avg_customer_satisfaction",
                    "risk_requests_count",
                    "risk_failed_requests",
                    "risk_request_failure_rate_pct",
                    "composite_risk_score",
                    "revenue_at_risk_usd",
                    "revenue_risk_band",
                ]
            )

        columns = [
            "customer_id",
            "renewal_risk_score",
            "support_ticket_count",
            "sla_compliance_pct",
            "reopen_rate_pct",
            "avg_resolution_hours",
            "avg_customer_satisfaction",
            "requests_count",
            "failed_requests",
            "request_failure_rate_pct",
            "composite_risk_score",
            "revenue_at_risk_usd",
            "revenue_risk_band",
        ]

        result = (
            dataframe[columns]
            .drop_duplicates(
                subset=["customer_id"]
            )
            .copy()
        )

        result = result.rename(
            columns={
                "renewal_risk_score":
                    "risk_view_renewal_score",
                "support_ticket_count":
                    "risk_support_ticket_count",
                "sla_compliance_pct":
                    "risk_sla_compliance_pct",
                "reopen_rate_pct":
                    "risk_reopen_rate_pct",
                "avg_resolution_hours":
                    "risk_avg_resolution_hours",
                "avg_customer_satisfaction":
                    "risk_avg_customer_satisfaction",
                "requests_count":
                    "risk_requests_count",
                "failed_requests":
                    "risk_failed_requests",
                "request_failure_rate_pct":
                    "risk_request_failure_rate_pct",
            }
        )

        return result

    # ========================================================
    # FEATURE ENGINEERING
    # ========================================================

    @staticmethod
    def _ratio(
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

        return pd.Series(
            np.where(
                denominator > 0,
                (
                    numerator
                    / denominator
                    * multiplier
                ),
                0.0,
            ),
            index=numerator.index,
        )

    def _engineer_features(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        data = dataframe.copy()

        # ----------------------------------------------------
        # TENURE
        # ----------------------------------------------------

        signup_date = pd.to_datetime(
            data["signup_date"],
            errors="coerce",
        )

        valid_signup_dates = (
            signup_date.dropna()
        )

        if valid_signup_dates.empty:
            reference_date = pd.Timestamp.today().normalize()
        else:
            reference_date = (
                valid_signup_dates.max()
                + pd.Timedelta(days=1)
            )

        data["customer_tenure_days"] = (
            reference_date
            - signup_date
        ).dt.days

        # ----------------------------------------------------
        # PROFITABILITY
        # ----------------------------------------------------

        data["gross_margin_pct"] = (
            self._ratio(
                data[
                    "lifetime_gross_profit_usd"
                ],
                data[
                    "lifetime_revenue_usd"
                ],
                100,
            )
        )

        data["revenue_per_transaction"] = (
            self._ratio(
                data[
                    "lifetime_revenue_usd"
                ],
                data["transactions"],
            )
        )

        data[
            "gross_profit_per_transaction"
        ] = self._ratio(
            data[
                "lifetime_gross_profit_usd"
            ],
            data["transactions"],
        )

        data["revenue_per_product"] = (
            self._ratio(
                data[
                    "lifetime_revenue_usd"
                ],
                data["purchased_products"],
            )
        )

        data["cloud_cost_to_revenue_pct"] = (
            self._ratio(
                data["cloud_cost_usd"],
                data[
                    "lifetime_revenue_usd"
                ],
                100,
            )
        )

        # ----------------------------------------------------
        # SUPPORT / QUALITY
        # ----------------------------------------------------

        data[
            "support_tickets_per_transaction"
        ] = self._ratio(
            data["support_tickets"],
            data["transactions"],
        )

        data["sla_breach_rate_pct"] = (
            self._ratio(
                data["sla_breaches"],
                data["support_tickets"],
                100,
            )
        )

        data["ticket_reopen_rate_pct"] = (
            self._ratio(
                data["reopened_tickets"],
                data["support_tickets"],
                100,
            )
        )

        data[
            "failed_request_rate_calculated_pct"
        ] = self._ratio(
            data["failed_requests"],
            data["requests_count"],
            100,
        )

        # ----------------------------------------------------
        # SUBSCRIPTIONS
        # ----------------------------------------------------

        data["active_subscription_pct"] = (
            self._ratio(
                data["active_subscriptions"],
                data["subscriptions"],
                100,
            )
        )

        data[
            "contract_value_per_active_subscription"
        ] = self._ratio(
            data[
                "active_contract_value_usd"
            ],
            data["active_subscriptions"],
        )

        # ----------------------------------------------------
        # AI INTENSITY
        # ----------------------------------------------------

        data[
            "ai_intensity_per_million_requests"
        ] = self._ratio(
            data["ai_tokens_million"],
            data["requests_count"],
            1_000_000,
        )

        return data

    # ========================================================
    # CLEANING
    # ========================================================

    def _clean_features(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        data = dataframe.copy()

        numeric_columns = [
            column
            for column in self.NUMERIC_FEATURES
            if column in data.columns
        ]

        for column in numeric_columns:

            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

            data[column] = (
                data[column]
                .replace(
                    [np.inf, -np.inf],
                    np.nan,
                )
                .fillna(0.0)
            )

        string_columns = [
            column
            for column
            in self.CATEGORICAL_FEATURES
            if (
                column in data.columns
                and column != "is_ai_customer"
            )
        ]

        for column in string_columns:

            data[column] = (
                data[column]
                .fillna("Unknown")
                .astype(str)
            )

        if "is_ai_customer" in data.columns:
            data["is_ai_customer"] = (
                data["is_ai_customer"]
                .fillna(False)
                .astype(bool)
            )

        return data

    # ========================================================
    # OUTPUT VALIDATION
    # ========================================================

    def _validate_output(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        if dataframe.empty:
            raise ValueError(
                "Customer feature dataset contains no rows."
            )

        if dataframe[
            "customer_id"
        ].isna().any():
            raise ValueError(
                "Customer feature dataset contains null customer_id values."
            )

        if dataframe[
            "customer_id"
        ].duplicated().any():
            raise ValueError(
                "Customer feature dataset must contain exactly "
                "one row per customer."
            )

        expected = {
            *self.IDENTIFIER_COLUMNS,
            *self.NUMERIC_FEATURES,
            *self.CATEGORICAL_FEATURES,
        }

        missing = sorted(
            expected
            - set(dataframe.columns)
        )

        if missing:
            raise ValueError(
                "Final customer feature dataset is missing columns: "
                + ", ".join(missing)
            )

        numeric_data = dataframe[
            self.NUMERIC_FEATURES
        ].to_numpy(
            dtype=float
        )

        if not np.isfinite(
            numeric_data
        ).all():
            raise ValueError(
                "Customer feature dataset contains "
                "NaN or infinite numeric values."
            )