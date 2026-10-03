from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.ml.churn_model import (
    ChurnModelTrainer,
)
from src.ml.churn_scoring import (
    CustomerChurnScorer,
)


ARTIFACT_DIR = Path("artifacts") / "ml"


def save_json(
    path: Path,
    payload: dict,
) -> None:

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            default=str,
        )


def feature_importance(
    bundle,
) -> pd.DataFrame:

    preprocessor = (
        bundle.pipeline.named_steps[
            "preprocessor"
        ]
    )

    model = (
        bundle.pipeline.named_steps["model"]
    )

    feature_names = (
        preprocessor.get_feature_names_out()
    )

    if hasattr(
        model,
        "feature_importances_",
    ):
        values = np.asarray(
            model.feature_importances_,
            dtype=float,
        )

    elif hasattr(
        model,
        "coef_",
    ):
        values = np.abs(
            np.asarray(
                model.coef_
            )[0]
        )

    else:
        # HistGradientBoosting has no native
        # feature_importances_ attribute.
        return pd.DataFrame(
            columns=[
                "feature",
                "importance",
                "importance_rank",
            ]
        )

    if len(values) != len(feature_names):
        raise ValueError(
            "Feature importance length mismatch."
        )

    result = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": values,
        }
    )

    result = result.sort_values(
        "importance",
        ascending=False,
    ).reset_index(drop=True)

    result["importance_rank"] = (
        np.arange(len(result)) + 1
    )

    return result


def main() -> None:

    print("=" * 72)
    print(
        "NEXUS 360 - HISTORICAL CHURN ML PIPELINE"
    )
    print("=" * 72)

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "\n[1/8] Building point-in-time "
        "historical dataset..."
    )

    trainer = ChurnModelTrainer()
    bundle = trainer.build()

    print(
        f"[OK] Observation cutoff : "
        f"{bundle.observation_cutoff.date()}"
    )

    print(
        f"[OK] Prediction end     : "
        f"{bundle.prediction_end.date()}"
    )

    print(
        f"[OK] Eligible customers : "
        f"{len(bundle.training_data):,}"
    )

    print(
        f"[OK] Model features     : "
        f"{len(bundle.feature_columns)}"
    )

    print(
        "\n[2/8] Candidate model evaluation..."
    )

    candidate_frame = pd.DataFrame(
        bundle.candidate_metrics
    )

    display_columns = [
        "model_name",
        "threshold",
        "roc_auc",
        "pr_auc",
        "precision",
        "recall",
        "f1",
    ]

    print(
        candidate_frame[
            display_columns
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    print(
        "\n[3/8] Best validation model..."
    )

    print(
        f"[OK] Selected model     : "
        f"{bundle.model_name}"
    )

    print(
        f"[OK] Decision threshold : "
        f"{bundle.threshold:.2f}"
    )

    validation = (
        bundle.validation_metrics.to_dict()
    )

    print(
        f"[OK] Validation ROC-AUC : "
        f"{validation['roc_auc']:.4f}"
    )

    print(
        f"[OK] Validation PR-AUC  : "
        f"{validation['pr_auc']:.4f}"
    )

    print(
        f"[OK] Validation F1      : "
        f"{validation['f1']:.4f}"
    )

    print(
        "\n[4/8] Untouched test evaluation..."
    )

    test = (
        bundle.test_metrics.to_dict()
    )

    for key in [
        "roc_auc",
        "pr_auc",
        "accuracy",
        "precision",
        "recall",
        "f1",
    ]:
        print(
            f"{key.upper():<12}: "
            f"{test[key]:.4f}"
        )

    print(
        "CONFUSION   : "
        f"TN={test['tn']} "
        f"FP={test['fp']} "
        f"FN={test['fn']} "
        f"TP={test['tp']}"
    )

    print(
        "\n[5/8] Generating customer scores..."
    )

    scorer = CustomerChurnScorer(
        bundle
    )

    scores = scorer.score()

    print(
        f"[OK] Scored customers: "
        f"{len(scores):,}"
    )

    print(
        "\n[6/8] Extracting explainability..."
    )

    importance = feature_importance(
        bundle
    )

    print(
        f"[OK] Importance rows: "
        f"{len(importance):,}"
    )

    print(
        "\n[7/8] Saving artifacts..."
    )

    joblib.dump(
        bundle.pipeline,
        ARTIFACT_DIR
        / "historical_churn_model.joblib",
    )

    scores.to_csv(
        ARTIFACT_DIR
        / "historical_customer_churn_scores.csv",
        index=False,
    )

    importance.to_csv(
        ARTIFACT_DIR
        / "historical_feature_importance.csv",
        index=False,
    )

    candidate_frame.to_csv(
        ARTIFACT_DIR
        / "historical_candidate_models.csv",
        index=False,
    )

    metrics = {
        "validation": validation,
        "test": test,
        "candidate_models": (
            bundle.candidate_metrics
        ),
    }

    save_json(
        ARTIFACT_DIR
        / "historical_model_metrics.json",
        metrics,
    )

    split_counts = (
        bundle.training_data[
            "dataset_split"
        ]
        .value_counts()
        .to_dict()
    )

    metadata = {
        "created_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "model_purpose": (
            "Predict whether a customer active "
            "at the observation cutoff will have "
            "no subscription in force at the end "
            "of the future prediction window."
        ),

        "observation_cutoff": (
            str(
                bundle.observation_cutoff.date()
            )
        ),

        "prediction_end": (
            str(
                bundle.prediction_end.date()
            )
        ),

        "selected_model": (
            bundle.model_name
        ),

        "decision_threshold": (
            bundle.threshold
        ),

        "rows": len(
            bundle.training_data
        ),

        "feature_count": len(
            bundle.feature_columns
        ),

        "feature_columns": (
            bundle.feature_columns
        ),

        "numeric_features": (
            bundle.numeric_features
        ),

        "categorical_features": (
            bundle.categorical_features
        ),

        "dataset_splits": (
            split_counts
        ),

        "historical_churn_rate": float(
            bundle.training_data[
                "churn_target"
            ].mean()
        ),
    }

    save_json(
        ARTIFACT_DIR
        / "historical_model_metadata.json",
        metadata,
    )

    print(
        "[OK] Production artifacts saved."
    )

    print(
        "\n[8/8] Risk portfolio summary..."
    )

    risk_distribution = (
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

    print()

    for band, count in (
        risk_distribution.items()
    ):
        print(
            f"{band:<10}: {count:,}"
        )

    if (
        "model_revenue_at_risk_usd"
        in scores.columns
    ):
        print(
            "\nProbability-weighted "
            "historical revenue at risk: "
            f"${scores['model_revenue_at_risk_usd'].sum():,.2f}"
        )

    print("\n" + "=" * 72)
    print(
        "[SUCCESS] Historical churn ML "
        "pipeline completed."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()