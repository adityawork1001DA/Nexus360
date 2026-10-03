from __future__ import annotations

import pandas as pd


class RevenueAnalyzer:

    @staticmethod
    def prepare_monthly_revenue(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        result = df.copy()

        date_candidates = [
            "month_start",
            "month",
            "revenue_month",
        ]

        for column in date_candidates:
            if column in result.columns:
                result[column] = pd.to_datetime(
                    result[column],
                    errors="coerce",
                )

        return result

    @staticmethod
    def concentration_metrics(
        customer_df: pd.DataFrame,
    ) -> dict[str, float]:

        revenue_column = None

        for candidate in (
            "customer_revenue_usd",
            "lifetime_revenue_usd",
            "net_revenue_usd",
        ):
            if candidate in customer_df.columns:
                revenue_column = candidate
                break

        if revenue_column is None:
            raise ValueError(
                "No supported customer revenue column found."
            )

        revenue = pd.to_numeric(
            customer_df[revenue_column],
            errors="coerce",
        ).fillna(0)

        total = revenue.sum()

        if total <= 0:
            return {
                "top_10_pct_share": 0.0,
                "top_20_pct_share": 0.0,
            }

        ordered = revenue.sort_values(
            ascending=False
        ).reset_index(drop=True)

        n = len(ordered)

        top10_count = max(1, int(n * 0.10))
        top20_count = max(1, int(n * 0.20))

        return {
            "top_10_pct_share": float(
                ordered.iloc[:top10_count].sum()
                / total
                * 100
            ),
            "top_20_pct_share": float(
                ordered.iloc[:top20_count].sum()
                / total
                * 100
            ),
        }

    @staticmethod
    def product_summary(
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        required = {
            "product_name",
            "net_revenue_usd",
        }

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {sorted(missing)}"
            )

        result = df.copy()

        result["net_revenue_usd"] = pd.to_numeric(
            result["net_revenue_usd"],
            errors="coerce",
        ).fillna(0)

        return (
            result.groupby(
                "product_name",
                as_index=False,
            )
            .agg(
                net_revenue_usd=(
                    "net_revenue_usd",
                    "sum",
                )
            )
            .sort_values(
                "net_revenue_usd",
                ascending=False,
            )
            .reset_index(drop=True)
        )