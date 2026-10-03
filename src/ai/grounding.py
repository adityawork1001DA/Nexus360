from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.ai.retriever import RetrievalBundle


@dataclass
class GroundingEvidence:
    metrics: dict[str, Any] = field(
        default_factory=dict
    )
    insights: list[str] = field(
        default_factory=list
    )
    definitions: dict[str, str] = field(
        default_factory=dict
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class NexusGroundingEngine:
    """
    Convert controlled retrieval results into compact,
    serializable evidence for Gemini.
    """

    MAX_SAMPLE_ROWS = 12
    MAX_COLUMNS = 30

    def build(
        self,
        bundle: RetrievalBundle,
    ) -> GroundingEvidence:

        if bundle.domain == "ml":
            return self._build_ml(
                bundle
            )

        return self._build_semantic(
            bundle
        )

    def _build_semantic(
        self,
        bundle: RetrievalBundle,
    ) -> GroundingEvidence:

        evidence = GroundingEvidence()

        evidence.metadata[
            "grounding_domain"
        ] = bundle.domain

        evidence.metadata[
            "retrieval_errors"
        ] = bundle.errors

        evidence.metadata[
            "available_views"
        ] = list(
            bundle.frames.keys()
        )

        for view_name, frame in bundle.frames.items():

            if frame.empty:
                continue

            prefix = self._metric_prefix(
                view_name
            )

            evidence.metrics[
                f"{prefix}_rows"
            ] = int(len(frame))

            numeric_columns = list(
                frame.select_dtypes(
                    include="number"
                ).columns
            )

            for column in numeric_columns[:10]:

                values = pd.to_numeric(
                    frame[column],
                    errors="coerce",
                ).dropna()

                if values.empty:
                    continue

                evidence.metrics[
                    f"{prefix}_{column}_sum"
                ] = self._safe_number(
                    values.sum()
                )

                evidence.metrics[
                    f"{prefix}_{column}_mean"
                ] = self._safe_number(
                    values.mean()
                )

            evidence.metadata[
                f"{prefix}_columns"
            ] = list(
                frame.columns[
                    : self.MAX_COLUMNS
                ]
            )

            evidence.metadata[
                f"{prefix}_sample"
            ] = self._records(
                frame.head(
                    self.MAX_SAMPLE_ROWS
                )
            )

            self._add_ranked_insight(
                evidence=evidence,
                view_name=view_name,
                frame=frame,
            )

        evidence.definitions.update(
            {
                "semantic_view": (
                    "An approved Nexus360 analytical dataset "
                    "used as controlled AI evidence."
                ),
                "grounded_answer": (
                    "An answer restricted to facts present "
                    "in the supplied Nexus360 evidence."
                ),
            }
        )

        return evidence

    def _build_ml(
        self,
        bundle: RetrievalBundle,
    ) -> GroundingEvidence:

        evidence = GroundingEvidence()

        data = bundle.ml

        scores = data.get(
            "scores",
            pd.DataFrame(),
        )

        importance = data.get(
            "importance",
            pd.DataFrame(),
        )

        summary = data.get(
            "summary",
            {},
        )

        metrics = data.get(
            "metrics",
            {},
        )

        for key, value in summary.items():

            if isinstance(
                value,
                (str, int, float, bool),
            ):
                evidence.metrics[key] = value

        test = metrics.get(
            "test",
            {},
        )

        for key in (
            "roc_auc",
            "pr_auc",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "tn",
            "fp",
            "fn",
            "tp",
        ):
            if key in test:
                evidence.metrics[
                    f"test_{key}"
                ] = test[key]

        if not scores.empty:

            wanted = [
                column
                for column in (
                    "customer_id",
                    "customer_name",
                    "customer_segment",
                    "industry",
                    "churn_probability",
                    "churn_probability_pct",
                    "predicted_churn",
                    "risk_band",
                    "expected_contract_value_at_risk_usd",
                    "risk_rank",
                )
                if column in scores.columns
            ]

            sort_column = None

            if "risk_rank" in scores.columns:
                top = scores.sort_values(
                    "risk_rank"
                ).head(15)

            elif "churn_probability" in scores.columns:
                sort_column = "churn_probability"

                top = scores.sort_values(
                    sort_column,
                    ascending=False,
                ).head(15)

            else:
                top = scores.head(15)

            evidence.metadata[
                "top_risk_customers"
            ] = self._records(
                top[wanted]
            )

            if (
                "risk_band"
                in scores.columns
            ):
                distribution = (
                    scores["risk_band"]
                    .value_counts()
                    .to_dict()
                )

                evidence.metadata[
                    "risk_distribution"
                ] = {
                    str(key): int(value)
                    for key, value
                    in distribution.items()
                }

            if not top.empty:

                names = []

                for _, row in top.head(5).iterrows():

                    customer = row.get(
                        "customer_name",
                        row.get(
                            "customer_id",
                            "Unknown customer",
                        ),
                    )

                    probability = row.get(
                        "churn_probability_pct"
                    )

                    if pd.notna(probability):
                        names.append(
                            f"{customer} "
                            f"({float(probability):.2f}%)"
                        )
                    else:
                        names.append(
                            str(customer)
                        )

                if names:
                    evidence.insights.append(
                        "Highest modeled churn-risk "
                        "customers: "
                        + ", ".join(names)
                        + "."
                    )

        if not importance.empty:

            columns = [
                column
                for column in (
                    "feature",
                    "importance",
                    "importance_rank",
                )
                if column in importance.columns
            ]

            top_importance = (
                importance.sort_values(
                    "importance_rank"
                )
                if "importance_rank"
                in importance.columns
                else importance
            ).head(15)

            evidence.metadata[
                "leading_model_features"
            ] = self._records(
                top_importance[columns]
            )

            if "feature" in top_importance.columns:

                features = (
                    top_importance[
                        "feature"
                    ]
                    .astype(str)
                    .head(8)
                    .tolist()
                )

                evidence.insights.append(
                    "Leading model features include: "
                    + ", ".join(features)
                    + "."
                )

        evidence.metadata[
            "grounding_domain"
        ] = "ml"

        evidence.metadata[
            "retrieval_errors"
        ] = bundle.errors

        evidence.definitions.update(
            {
                "churn_probability": (
                    "A model-estimated probability of churn; "
                    "it is not a guaranteed future outcome."
                ),
                "risk_band": (
                    "A portfolio prioritization category based "
                    "on modeled churn risk."
                ),
                "roc_auc": (
                    "A ranking metric measuring how well the "
                    "model separates churn and non-churn cases."
                ),
                "pr_auc": (
                    "Precision-recall area under the curve; "
                    "especially useful for imbalanced targets."
                ),
                "precision": (
                    "Among customers predicted to churn, the "
                    "share that actually churned historically."
                ),
                "recall": (
                    "Among customers that actually churned, "
                    "the share detected by the model."
                ),
            }
        )

        return evidence

    def _add_ranked_insight(
        self,
        *,
        evidence: GroundingEvidence,
        view_name: str,
        frame: pd.DataFrame,
    ) -> None:

        numeric = list(
            frame.select_dtypes(
                include="number"
            ).columns
        )

        text_columns = [
            column
            for column in frame.columns
            if column not in numeric
        ]

        if not numeric or not text_columns:
            return

        metric = numeric[0]
        label = text_columns[0]

        ranked = frame[
            [label, metric]
        ].copy()

        ranked[metric] = pd.to_numeric(
            ranked[metric],
            errors="coerce",
        )

        ranked = ranked.dropna(
            subset=[metric]
        )

        if ranked.empty:
            return

        row = ranked.sort_values(
            metric,
            ascending=False,
        ).iloc[0]

        evidence.insights.append(
            f"In {view_name}, the highest observed "
            f"{metric} row is {row[label]} "
            f"with {self._safe_number(row[metric])}."
        )

    @staticmethod
    def _metric_prefix(
        view_name: str,
    ) -> str:

        return (
            view_name
            .removeprefix("v_")
            .replace("-", "_")
        )

    @classmethod
    def _records(
        cls,
        frame: pd.DataFrame,
    ) -> list[dict[str, Any]]:

        clean = frame.copy()

        clean = clean.replace(
            {
                np.nan: None,
                np.inf: None,
                -np.inf: None,
            }
        )

        records = clean.to_dict(
            orient="records"
        )

        return [
            {
                str(key): cls._safe_value(value)
                for key, value in row.items()
            }
            for row in records
        ]

    @staticmethod
    def _safe_number(
        value: Any,
    ) -> int | float | None:

        try:
            numeric = float(value)

        except (TypeError, ValueError):
            return None

        if not math.isfinite(numeric):
            return None

        if numeric.is_integer():
            return int(numeric)

        return round(
            numeric,
            4,
        )

    @classmethod
    def _safe_value(
        cls,
        value: Any,
    ) -> Any:

        if value is None:
            return None

        if isinstance(
            value,
            (
                np.integer,
                int,
            ),
        ):
            return int(value)

        if isinstance(
            value,
            (
                np.floating,
                float,
            ),
        ):
            return cls._safe_number(
                value
            )

        if isinstance(
            value,
            (
                pd.Timestamp,
                np.datetime64,
            ),
        ):
            return str(value)

        if isinstance(
            value,
            (str, bool),
        ):
            return value

        return str(value)