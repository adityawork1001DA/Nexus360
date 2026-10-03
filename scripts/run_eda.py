from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.analytics.customer_analysis import CustomerAnalyzer
from src.analytics.data_loader import AnalyticsDataLoader
from src.analytics.profiler import DataProfiler
from src.analytics.statistics import StatisticalAnalyzer
from src.analytics.visualization import AnalyticsVisualizer


REPORT_ROOT = Path("reports")
PROFILE_DIR = REPORT_ROOT / "profiling"
EXPORT_DIR = REPORT_ROOT / "exports"
FIGURE_DIR = REPORT_ROOT / "figures"


def ensure_directories() -> None:

    for directory in (
        PROFILE_DIR,
        EXPORT_DIR,
        FIGURE_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def save_dataframe(
    df: pd.DataFrame,
    filename: str,
) -> Path:

    path = EXPORT_DIR / filename

    df.to_csv(
        path,
        index=False,
    )

    return path


def main() -> None:

    ensure_directories()

    print("=" * 72)
    print("NEXUS 360 - PYTHON ANALYTICS & EDA ENGINE")
    print("=" * 72)

    loader = AnalyticsDataLoader()
    profiler = DataProfiler()
    statistics = StatisticalAnalyzer()

    visualizer = AnalyticsVisualizer(
        FIGURE_DIR
    )

    print("\n[1/7] Loading semantic datasets...")

    monthly_revenue = loader.load_view(
        "v_monthly_revenue"
    )

    customer_360 = loader.load_view(
        "v_customer_360"
    )

    revenue_risk = loader.load_view(
        "v_revenue_at_risk"
    )

    market_opportunity = loader.load_view(
        "v_market_opportunity"
    )

    cloud_finops = loader.load_view(
        "v_cloud_finops"
    )

    business_health = loader.load_view(
        "v_business_health_score"
    )

    datasets = {
        "monthly_revenue": monthly_revenue,
        "customer_360": customer_360,
        "revenue_risk": revenue_risk,
        "market_opportunity": market_opportunity,
        "cloud_finops": cloud_finops,
        "business_health": business_health,
    }

    print("[OK] Semantic datasets loaded.")

    print("\n[2/7] Running data profiling...")

    profile_index = {}

    for name, dataframe in datasets.items():

        profile = profiler.profile(dataframe)

        profile_path = (
            PROFILE_DIR
            / f"{name}_profile.json"
        )

        profiler.export_json(
            profile,
            profile_path,
        )

        profile_index[name] = {
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
            "profile": str(profile_path),
        }

    with (
        PROFILE_DIR / "profile_index.json"
    ).open("w", encoding="utf-8") as file:

        json.dump(
            profile_index,
            file,
            indent=2,
        )

    print("[OK] Profiles generated.")

    print("\n[3/7] Exporting analytical datasets...")

    for name, dataframe in datasets.items():
        save_dataframe(
            dataframe,
            f"{name}.csv",
        )

    print("[OK] CSV analytical exports generated.")

    print("\n[4/7] Customer risk analysis...")

    risk_summary = CustomerAnalyzer.risk_summary(
        revenue_risk
    )

    segment_summary = CustomerAnalyzer.segment_summary(
        revenue_risk
    )

    save_dataframe(
        risk_summary,
        "customer_risk_summary.csv",
    )

    save_dataframe(
        segment_summary,
        "customer_segment_summary.csv",
    )

    print("[OK] Customer analytics generated.")

    print("\n[5/7] Statistical analysis...")

    cloud_correlation = (
        statistics.correlation_matrix(
            cloud_finops
        )
    )

    save_dataframe(
        cloud_correlation.reset_index(),
        "cloud_correlation_matrix.csv",
    )

    numeric_summary = profiler.numeric_summary(
        customer_360
    )

    save_dataframe(
        numeric_summary.reset_index(),
        "customer_numeric_summary.csv",
    )

    print("[OK] Statistical outputs generated.")

    print("\n[6/7] Creating visualizations...")

    date_candidates = [
        "month_start",
        "month",
        "revenue_month",
    ]

    revenue_candidates = [
        "net_revenue_usd",
        "monthly_revenue_usd",
        "total_revenue_usd",
    ]

    date_column = next(
        (
            column
            for column in date_candidates
            if column in monthly_revenue.columns
        ),
        None,
    )

    revenue_column = next(
        (
            column
            for column in revenue_candidates
            if column in monthly_revenue.columns
        ),
        None,
    )

    if date_column and revenue_column:
        visualizer.revenue_trend(
            monthly_revenue,
            date_column,
            revenue_column,
        )

    visualizer.risk_distribution(
        revenue_risk
    )

    visualizer.market_opportunity(
        market_opportunity
    )

    if not cloud_correlation.empty:
        visualizer.correlation_heatmap(
            cloud_correlation
        )

    print("[OK] Visualizations generated.")

    print("\n[7/7] Executive health snapshot...")

    if not business_health.empty:

        health_record = (
            business_health
            .iloc[0]
            .to_dict()
        )

        health_path = (
            EXPORT_DIR
            / "business_health_snapshot.json"
        )

        with health_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                health_record,
                file,
                indent=2,
                default=str,
            )

    print("[OK] Executive snapshot generated.")

    print("\n" + "=" * 72)
    print("NEXUS 360 PYTHON ANALYTICS COMPLETED")
    print("=" * 72)

    print(
        f"Datasets analysed : {len(datasets)}"
    )
    print(
        f"Profiles directory: {PROFILE_DIR}"
    )
    print(
        f"Exports directory : {EXPORT_DIR}"
    )
    print(
        f"Figures directory : {FIGURE_DIR}"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()