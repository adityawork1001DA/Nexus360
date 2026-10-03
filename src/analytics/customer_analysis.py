from __future__ import annotations

import pandas as pd


class CustomerAnalyzer:

    @staticmethod
    def risk_summary(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        required = {
            "revenue_risk_band",
            "revenue_at_risk_usd",
        }

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        result = df.copy()

        result["revenue_at_risk_usd"] = pd.to_numeric(
            result["revenue_at_risk_usd"],
            errors="coerce",
        ).fillna(0)

        summary = (
            result.groupby(
                "revenue_risk_band",
                dropna=False,
                as_index=False,
            )
            .agg(
                customer_count=(
                    "revenue_risk_band",
                    "size",
                ),
                revenue_at_risk_usd=(
                    "revenue_at_risk_usd",
                    "sum",
                ),
            )
        )

        return summary.sort_values(
            "revenue_at_risk_usd",
            ascending=False,
        ).reset_index(drop=True)

    @staticmethod
    def segment_summary(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        required = {
            "customer_segment",
            "lifetime_revenue_usd",
        }

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        result = df.copy()

        result["lifetime_revenue_usd"] = pd.to_numeric(
            result["lifetime_revenue_usd"],
            errors="coerce",
        ).fillna(0)

        return (
            result.groupby(
                "customer_segment",
                dropna=False,
                as_index=False,
            )
            .agg(
                customer_count=(
                    "customer_segment",
                    "size",
                ),
                lifetime_revenue_usd=(
                    "lifetime_revenue_usd",
                    "sum",
                ),
                average_customer_revenue_usd=(
                    "lifetime_revenue_usd",
                    "mean",
                ),
            )
            .sort_values(
                "lifetime_revenue_usd",
                ascending=False,
            )
            .reset_index(drop=True)
        )