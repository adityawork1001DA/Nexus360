from __future__ import annotations

import json
from pathlib import Path

from src.analytics.data_loader import AnalyticsDataLoader
from src.ml.anomaly_detection import RevenueAnomalyDetector
from src.ml.common import (
    ensure_ml_directories,
    utc_timestamp,
    write_json,
)
from src.ml.renewal_model import RenewalRiskModel
from src.ml.revenue_forecasting import RevenueForecaster
from src.ml.risk_regression import RevenueRiskRegressor


ARTIFACT_DIR = Path("models/artifacts")
REGISTRY_DIR = Path("models/registry")
METRIC_DIR = Path("reports/ml")
PREDICTION_DIR = Path("reports/predictions")


def main() -> None:

    ensure_ml_directories()

    print("=" * 76)
    print("NEXUS 360 - PREDICTIVE ANALYTICS & ML ENGINE")
    print("=" * 76)

    loader = AnalyticsDataLoader()

    print("\n[1/5] Loading ML source datasets...")

    subscription = loader.load_view(
        "v_subscription_renewal_risk"
    )

    revenue_risk = loader.load_view(
        "v_revenue_at_risk"
    )

    monthly_revenue = loader.load_view(
        "v_monthly_revenue"
    )

    anomalies = loader.load_view(
        "v_revenue_anomalies"
    )

    print("[OK] ML datasets loaded.")

    registry = {
        "registry_version": "1.0",
        "generated_at_utc": utc_timestamp(),
        "models": {},
    }

    # --------------------------------------------------------
    # Renewal classification
    # --------------------------------------------------------

    print(
        "\n[2/5] Training subscription renewal-risk classifier..."
    )

    renewal = RenewalRiskModel()

    renewal_metrics = renewal.train(
        subscription
    )

    renewal_path = renewal.save(
        ARTIFACT_DIR
        / "renewal_risk_classifier.joblib"
    )

    renewal_predictions = renewal.predict(
        subscription
    )

    renewal_predictions.to_csv(
        PREDICTION_DIR
        / "renewal_risk_predictions.csv",
        index=False,
    )

    write_json(
        renewal_metrics,
        METRIC_DIR
        / "renewal_risk_metrics.json",
    )

    registry["models"][
        "renewal_risk_classifier"
    ] = {
        "artifact": str(renewal_path),
        "metrics": renewal_metrics,
    }

    print("[OK] Renewal classifier trained.")

    # --------------------------------------------------------
    # Revenue at risk regression
    # --------------------------------------------------------

    print(
        "\n[3/5] Training revenue-at-risk regressor..."
    )

    risk_model = RevenueRiskRegressor()

    risk_metrics = risk_model.train(
        revenue_risk
    )

    risk_path = risk_model.save(
        ARTIFACT_DIR
        / "revenue_at_risk_regressor.joblib"
    )

    risk_predictions = risk_model.predict(
        revenue_risk
    )

    risk_predictions.to_csv(
        PREDICTION_DIR
        / "revenue_at_risk_predictions.csv",
        index=False,
    )

    write_json(
        risk_metrics,
        METRIC_DIR
        / "revenue_at_risk_metrics.json",
    )

    registry["models"][
        "revenue_at_risk_regressor"
    ] = {
        "artifact": str(risk_path),
        "metrics": risk_metrics,
    }

    print("[OK] Revenue-at-risk model trained.")

    # --------------------------------------------------------
    # Revenue forecasting
    # --------------------------------------------------------

    print(
        "\n[4/5] Training monthly revenue forecaster..."
    )

    forecaster = RevenueForecaster()

    forecast_metrics = forecaster.train(
        monthly_revenue
    )

    forecast_path = forecaster.save(
        ARTIFACT_DIR
        / "monthly_revenue_forecaster.joblib"
    )

    forecast = forecaster.forecast(
        periods=6
    )

    forecast.to_csv(
        PREDICTION_DIR
        / "monthly_revenue_forecast.csv",
        index=False,
    )

    write_json(
        forecast_metrics,
        METRIC_DIR
        / "monthly_revenue_forecast_metrics.json",
    )

    registry["models"][
        "monthly_revenue_forecaster"
    ] = {
        "artifact": str(forecast_path),
        "metrics": forecast_metrics,
    }

    print("[OK] Revenue forecaster trained.")

    # --------------------------------------------------------
    # Anomaly detection
    # --------------------------------------------------------

    print(
        "\n[5/5] Training revenue anomaly detector..."
    )

    anomaly_model = RevenueAnomalyDetector()

    anomaly_result = anomaly_model.fit_predict(
        anomalies
    )

    anomaly_path = anomaly_model.save(
        ARTIFACT_DIR
        / "revenue_anomaly_detector.joblib"
    )

    anomaly_result.to_csv(
        PREDICTION_DIR
        / "revenue_anomaly_predictions.csv",
        index=False,
    )

    write_json(
        anomaly_model.metrics,
        METRIC_DIR
        / "revenue_anomaly_metrics.json",
    )

    registry["models"][
        "revenue_anomaly_detector"
    ] = {
        "artifact": str(anomaly_path),
        "metrics": anomaly_model.metrics,
    }

    print("[OK] Revenue anomaly detector trained.")

    registry_path = (
        REGISTRY_DIR
        / "model_registry.json"
    )

    write_json(
        registry,
        registry_path,
    )

    print("\n" + "=" * 76)
    print("NEXUS 360 ML TRAINING COMPLETED")
    print("-" * 76)
    print(
        f"Models trained      : {len(registry['models'])}"
    )
    print(
        f"Artifacts directory : {ARTIFACT_DIR}"
    )
    print(
        f"Metrics directory   : {METRIC_DIR}"
    )
    print(
        f"Predictions         : {PREDICTION_DIR}"
    )
    print(
        f"Model registry      : {registry_path}"
    )
    print("=" * 76)


if __name__ == "__main__":
    main()