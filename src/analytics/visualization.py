from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class AnalyticsVisualizer:

    def __init__(
        self,
        output_dir: str | Path = "reports/figures",
    ) -> None:

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        sns.set_theme(style="whitegrid")

    def revenue_trend(
        self,
        df: pd.DataFrame,
        date_column: str,
        revenue_column: str,
        filename: str = "monthly_revenue_trend.png",
    ) -> Path:

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[revenue_column] = pd.to_numeric(
            data[revenue_column],
            errors="coerce",
        )

        data = data.dropna(
            subset=[date_column, revenue_column]
        ).sort_values(date_column)

        fig, ax = plt.subplots(figsize=(12, 6))

        sns.lineplot(
            data=data,
            x=date_column,
            y=revenue_column,
            marker="o",
            ax=ax,
        )

        ax.set_title(
            "Nexus 360 Monthly Revenue Trend"
        )
        ax.set_xlabel("Month")
        ax.set_ylabel("Revenue (USD)")

        fig.tight_layout()

        path = self.output_dir / filename

        fig.savefig(
            path,
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)

        return path

    def risk_distribution(
        self,
        df: pd.DataFrame,
        filename: str = "customer_risk_distribution.png",
    ) -> Path:

        data = df.copy()

        fig, ax = plt.subplots(figsize=(10, 6))

        order = [
            "Critical",
            "High",
            "Medium",
            "Low",
        ]

        sns.countplot(
            data=data,
            x="revenue_risk_band",
            order=[
                x
                for x in order
                if x in set(
                    data["revenue_risk_band"].dropna()
                )
            ],
            ax=ax,
        )

        ax.set_title(
            "Customer Revenue Risk Distribution"
        )
        ax.set_xlabel("Risk Band")
        ax.set_ylabel("Customers")

        fig.tight_layout()

        path = self.output_dir / filename

        fig.savefig(
            path,
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)

        return path

    def market_opportunity(
        self,
        df: pd.DataFrame,
        filename: str = "market_opportunity.png",
    ) -> Path:

        data = df.copy()

        data["market_opportunity_score"] = pd.to_numeric(
            data["market_opportunity_score"],
            errors="coerce",
        )

        data = (
            data.dropna(
                subset=["market_opportunity_score"]
            )
            .sort_values(
                "market_opportunity_score",
                ascending=False,
            )
        )

        fig, ax = plt.subplots(figsize=(12, 7))

        sns.barplot(
            data=data,
            y="country_name",
            x="market_opportunity_score",
            ax=ax,
        )

        ax.set_title(
            "Global Market Opportunity Index"
        )
        ax.set_xlabel("Opportunity Score")
        ax.set_ylabel("Country")

        fig.tight_layout()

        path = self.output_dir / filename

        fig.savefig(
            path,
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)

        return path

    def correlation_heatmap(
        self,
        correlation: pd.DataFrame,
        filename: str = "correlation_heatmap.png",
    ) -> Path:

        fig, ax = plt.subplots(figsize=(12, 9))

        sns.heatmap(
            correlation,
            cmap="coolwarm",
            center=0,
            ax=ax,
        )

        ax.set_title(
            "Nexus 360 Correlation Matrix"
        )

        fig.tight_layout()

        path = self.output_dir / filename

        fig.savefig(
            path,
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)

        return path