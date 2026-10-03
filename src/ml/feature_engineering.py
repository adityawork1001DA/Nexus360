from __future__ import annotations

import numpy as np
import pandas as pd


class FeatureEngineer:
    """
    Central feature-engineering layer for Nexus 360 ML workloads.
    """

    RENEWAL_CATEGORICAL = [
        "customer_segment",
        "industry",
        "product_family",
        "billing_frequency",
    ]

    RENEWAL_NUMERIC = [
        "contract_value_usd",
        "seats",
        "subscription_tenure_days",
        "days_to_contract_end",
    ]

    RISK_CATEGORICAL = [
        "customer_segment",
        "industry",
        "customer_status",
    ]

    RISK_NUMERIC = [
        "is_ai_customer",
        "lifetime_revenue_usd",
        "renewal_risk_score",
        "support_ticket_count",
        "sla_compliance_pct",
        "reopen_rate_pct",
        "avg_resolution_hours",
        "avg_customer_satisfaction",
        "requests_count",
        "failed_requests",
        "request_failure_rate_pct",
    ]

    @staticmethod
    def renewal_dataset(
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:

        data = df.copy()

        start = pd.to_datetime(
            data["subscription_start_date"],
            errors="coerce",
        )

        end = pd.to_datetime(
            data["subscription_end_date"],
            errors="coerce",
        )

        data["subscription_tenure_days"] = (
            end - start
        ).dt.days.clip(lower=0)

        reference_date = end.max()

        if pd.isna(reference_date):
            reference_date = pd.Timestamp.today().normalize()

        data["days_to_contract_end"] = (
            end - reference_date
        ).dt.days

        data["days_to_contract_end"] = (
            data["days_to_contract_end"]
            .fillna(0)
            .clip(lower=0)
        )

        # Proxy label derived from current operational status.
        # We intentionally DO NOT use renewal_risk_score/band as features.
        risky_statuses = {
            "cancelled",
            "canceled",
            "expired",
            "inactive",
            "suspended",
            "terminated",
            "non-renewed",
            "non renewed",
            "churned",
        }

        status = (
            data["subscription_status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        auto_renew = (
            data["auto_renew"]
            .fillna(False)
            .astype(bool)
        )

        target = (
            status.isin(risky_statuses)
            | (~auto_renew)
        ).astype(int)

        feature_columns = (
            FeatureEngineer.RENEWAL_CATEGORICAL
            + FeatureEngineer.RENEWAL_NUMERIC
        )

        X = data[feature_columns].copy()

        identifiers = data[
            [
                "subscription_id",
                "customer_id",
                "customer_name",
                "product_code",
                "product_name",
            ]
        ].copy()

        return X, target, identifiers

    @staticmethod
    def revenue_risk_dataset(
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:

        data = df.copy()

        data["is_ai_customer"] = (
            data["is_ai_customer"]
            .fillna(False)
            .astype(int)
        )

        X = data[
            FeatureEngineer.RISK_CATEGORICAL
            + FeatureEngineer.RISK_NUMERIC
        ].copy()

        y = pd.to_numeric(
            data["revenue_at_risk_usd"],
            errors="coerce",
        ).fillna(0.0)

        identifiers = data[
            [
                "customer_id",
                "customer_name",
            ]
        ].copy()

        return X, y, identifiers

    @staticmethod
    def forecasting_dataset(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        data = df.copy()

        data["revenue_month"] = pd.to_datetime(
            data["revenue_month"],
            errors="coerce",
        )

        data["net_revenue_usd"] = pd.to_numeric(
            data["net_revenue_usd"],
            errors="coerce",
        )

        data = (
            data.dropna(
                subset=[
                    "revenue_month",
                    "net_revenue_usd",
                ]
            )
            .sort_values("revenue_month")
            .reset_index(drop=True)
        )

        data["time_index"] = np.arange(len(data))

        data["month_number"] = (
            data["revenue_month"].dt.month
        )

        data["quarter"] = (
            data["revenue_month"].dt.quarter
        )

        data["lag_1"] = (
            data["net_revenue_usd"].shift(1)
        )

        data["lag_2"] = (
            data["net_revenue_usd"].shift(2)
        )

        data["lag_3"] = (
            data["net_revenue_usd"].shift(3)
        )

        data["rolling_mean_3"] = (
            data["net_revenue_usd"]
            .shift(1)
            .rolling(3)
            .mean()
        )

        data["rolling_mean_6"] = (
            data["net_revenue_usd"]
            .shift(1)
            .rolling(6)
            .mean()
        )

        return data