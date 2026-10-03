from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


from src.ml.current_customer_features import (
    CurrentCustomerFeatureBuilder,
)


ARTIFACT_DIR = Path("artifacts") / "ml"

MODEL_PATH = (
    ARTIFACT_DIR
    / "historical_churn_model.joblib"
)

METADATA_PATH = (
    ARTIFACT_DIR
    / "historical_model_metadata.json"
)

OUTPUT_PATH = (
    ARTIFACT_DIR
    / "current_customer_churn_scores.csv"
)

SUMMARY_PATH = (
    ARTIFACT_DIR
    / "current_churn_summary.json"
)


def risk_band(
    probability: float,
    threshold: float,
) -> str:
    """
    Risk bands aligned with the validated production threshold.
    """

    if probability >= threshold:
        return "Critical"

    if probability >= threshold * 0.625:
        return "High"

    if probability >= threshold * 0.25:
        return "Medium"

    return "Low"


def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing ML metadata: {METADATA_PATH}. "
            "Run python -m scripts.run_ml first."
        )

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main() -> None:
    print("=" * 72)
    print(
        "NEXUS 360 - CURRENT CUSTOMER CHURN SCORING"
    )
    print("=" * 72)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Missing trained model: {MODEL_PATH}. "
            "Run python -m scripts.run_ml first."
        )

    print(
        "\n[1/6] Loading validated historical model..."
    )

    pipeline = joblib.load(
        MODEL_PATH
    )

    metadata = load_metadata()

    threshold = float(
        metadata["decision_threshold"]
    )

    trained_features = list(
        metadata["feature_columns"]
    )

    print(
        f"[OK] Model             : "
        f"{metadata['selected_model']}"
    )

    print(
        f"[OK] Threshold         : "
        f"{threshold:.2f}"
    )

    print(
        f"[OK] Training cutoff   : "
        f"{metadata['observation_cutoff']}"
    )

    print(
        "\n[2/6] Building latest customer snapshot..."
    )

    current_bundle = (
        CurrentCustomerFeatureBuilder().build()
    )

    data = current_bundle.features.copy()

    print(
        f"[OK] Scoring cutoff    : "
        f"{current_bundle.scoring_cutoff.date()}"
    )

    print(
        f"[OK] Eligible customers: "
        f"{len(data):,}"
    )

    print(
        "\n[3/6] Validating training-serving schema..."
    )

    missing_features = [
        column
        for column in trained_features
        if column not in data.columns
    ]

    if missing_features:
        raise ValueError(
            "Current scoring snapshot is missing "
            f"trained features: {missing_features}"
        )

    unexpected_training_features = [
        column
        for column in current_bundle.feature_columns
        if column not in trained_features
    ]

    if unexpected_training_features:
        print(
            "[INFO] Additional current features ignored: "
            f"{unexpected_training_features}"
        )

    X = data[trained_features].copy()

    if X.shape[1] != len(trained_features):
        raise ValueError(
            "Training-serving feature count mismatch."
        )

    print(
        f"[OK] Feature schema    : "
        f"{len(trained_features)} features"
    )

    print(
        "\n[4/6] Predicting current churn risk..."
    )

    probabilities = (
        pipeline.predict_proba(X)[:, 1]
    )

    if not np.isfinite(
        probabilities
    ).all():
        raise ValueError(
            "Model generated non-finite probabilities."
        )

    predictions = (
        probabilities >= threshold
    ).astype(int)

    identity_columns = [
        column
        for column in [
            "customer_id",
            "customer_name",
            "customer_segment",
            "industry",
            "customer_status",
            "is_ai_customer",
            "trailing_revenue_usd",
            "trailing_gross_profit_usd",
            "trailing_transactions",
            "trailing_support_tickets",
            "trailing_sla_breach_rate_pct",
            "trailing_request_failure_rate_pct",
            "historical_subscription_count",
            "subscriptions_in_force_at_cutoff",
            "contract_value_in_force_at_cutoff",
            "historical_auto_renew_pct",
            "customer_tenure_days_at_cutoff",
            "log_customer_tenure_days",
        ]
        if column in data.columns
    ]

    scores = data[
        identity_columns
    ].copy()

    scores[
        "churn_probability"
    ] = probabilities

    scores[
        "churn_probability_pct"
    ] = (
        probabilities * 100.0
    ).round(2)

    scores[
        "predicted_churn"
    ] = predictions

    scores["risk_band"] = [
        risk_band(
            probability=float(probability),
            threshold=threshold,
        )
        for probability in probabilities
    ]

    if (
        "contract_value_in_force_at_cutoff"
        in scores.columns
    ):
        scores[
            "expected_contract_value_at_risk_usd"
        ] = (
            scores[
                "contract_value_in_force_at_cutoff"
            ]
            .fillna(0.0)
            .clip(lower=0.0)
            * scores[
                "churn_probability"
            ]
        ).round(2)

    scores["risk_rank"] = (
        scores["churn_probability"]
        .rank(
            method="first",
            ascending=False,
        )
        .astype(int)
    )

    scores[
        "scoring_cutoff"
    ] = current_bundle.scoring_cutoff.date()

    scores[
        "model_training_cutoff"
    ] = metadata[
        "observation_cutoff"
    ]

    scores = scores.sort_values(
        [
            "churn_probability",
            "risk_rank",
        ],
        ascending=[
            False,
            True,
        ],
    ).reset_index(drop=True)

    print(
        f"[OK] Predictions       : "
        f"{len(scores):,}"
    )

    print(
        "\n[5/6] Saving current scoring artifacts..."
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    scores.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    distribution = (
        scores["risk_band"]
        .value_counts()
        .reindex(
            [
                "Critical",
                "High",
                "Medium",
                "Low",
            ],
            fill_value=0,
        )
    )

    summary = {
        "scoring_cutoff": str(
            current_bundle.scoring_cutoff.date()
        ),
        "model_training_cutoff": metadata[
            "observation_cutoff"
        ],
        "model_prediction_end": metadata[
            "prediction_end"
        ],
        "selected_model": metadata[
            "selected_model"
        ],
        "decision_threshold": threshold,
        "customers_scored": int(
            len(scores)
        ),
        "predicted_churn_customers": int(
            predictions.sum()
        ),
        "predicted_churn_rate_pct": round(
            float(predictions.mean() * 100.0),
            2,
        ),
        "average_churn_probability_pct": round(
            float(probabilities.mean() * 100.0),
            2,
        ),
        "risk_distribution": {
            str(key): int(value)
            for key, value
            in distribution.items()
        },
    }

    if (
        "expected_contract_value_at_risk_usd"
        in scores.columns
    ):
        summary[
            "expected_contract_value_at_risk_usd"
        ] = round(
            float(
                scores[
                    "expected_contract_value_at_risk_usd"
                ].sum()
            ),
            2,
        )

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
        )

    print(
        f"[OK] Scores  : {OUTPUT_PATH}"
    )

    print(
        f"[OK] Summary : {SUMMARY_PATH}"
    )

    print(
        "\n[6/6] Current risk portfolio..."
    )

    print()

    for band, count in (
        distribution.items()
    ):
        print(
            f"{band:<10}: {count:,}"
        )

    print(
        "\nPredicted churn customers : "
        f"{predictions.sum():,}"
    )

    print(
        "Predicted churn rate      : "
        f"{predictions.mean() * 100:.2f}%"
    )

    print(
        "Average churn probability : "
        f"{probabilities.mean() * 100:.2f}%"
    )

    if (
        "expected_contract_value_at_risk_usd"
        in scores.columns
    ):
        print(
            "Expected contract value "
            "at risk : "
            f"${scores['expected_contract_value_at_risk_usd'].sum():,.2f}"
        )

    print(
        "\nTop 10 current-risk customers:"
    )

    top_columns = [
        column
        for column in [
            "customer_id",
            "customer_name",
            "customer_segment",
            "churn_probability_pct",
            "risk_band",
            "contract_value_in_force_at_cutoff",
            "expected_contract_value_at_risk_usd",
        ]
        if column in scores.columns
    ]

    print(
        scores[
            top_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print("\n" + "=" * 72)
    print(
        "[SUCCESS] Current customer churn "
        "scoring completed."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()