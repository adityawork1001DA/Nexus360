from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd
import streamlit as st

from src.analytics.data_loader import AnalyticsDataLoader


# ============================================================
# PATHS
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ML_ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "ml"

CURRENT_CHURN_SCORES_PATH = (
    ML_ARTIFACT_DIR / "current_customer_churn_scores.csv"
)

CURRENT_CHURN_SUMMARY_PATH = (
    ML_ARTIFACT_DIR / "current_churn_summary.json"
)

HISTORICAL_MODEL_METRICS_PATH = (
    ML_ARTIFACT_DIR / "historical_model_metrics.json"
)

HISTORICAL_FEATURE_IMPORTANCE_PATH = (
    ML_ARTIFACT_DIR / "historical_feature_importance.csv"
)


# ============================================================
# GENERIC ANALYTICS ACCESS
# ============================================================


@st.cache_data(ttl=300, show_spinner=False)
def load_analytics_view(
    view_name: str,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Load an approved analytics semantic-layer view.

    Streamlit cache keeps dashboard navigation responsive while
    preserving the AnalyticsDataLoader allow-list security model.
    """

    loader = AnalyticsDataLoader()

    return loader.load_view(
        view_name=view_name,
        limit=limit,
    )


def clear_dashboard_cache() -> None:
    """
    Clear Streamlit cached analytical datasets and ML artifacts.
    """

    st.cache_data.clear()


# ============================================================
# EXECUTIVE DASHBOARD
# ============================================================


def load_executive_bundle() -> dict[str, pd.DataFrame]:
    """
    Load datasets required by the Executive Command Center.
    """

    return {
        "executive": load_analytics_view(
            "v_executive_kpis"
        ),
        "monthly": load_analytics_view(
            "v_monthly_revenue"
        ),
        "regional": load_analytics_view(
            "v_regional_performance"
        ),
        "products": load_analytics_view(
            "v_product_revenue_rank"
        ),
        "risk": load_analytics_view(
            "v_revenue_at_risk"
        ),
        "business_health": load_analytics_view(
            "v_business_health_score"
        ),
    }


# ============================================================
# CUSTOMER INTELLIGENCE
# ============================================================


def load_customer_bundle() -> dict[str, pd.DataFrame]:
    """
    Load the complete Customer Intelligence semantic bundle.
    """

    return {
        "customer_360": load_analytics_view(
            "v_customer_360"
        ),
        "rfm": load_analytics_view(
            "v_customer_rfm"
        ),
        "pareto": load_analytics_view(
            "v_customer_pareto"
        ),
        "value_tiers": load_analytics_view(
            "v_customer_value_tiers"
        ),
        "cohort": load_analytics_view(
            "v_customer_cohort"
        ),
        "subscription_health": load_analytics_view(
            "v_subscription_health"
        ),
        "renewal_risk": load_analytics_view(
            "v_subscription_renewal_risk"
        ),
        "revenue_at_risk": load_analytics_view(
            "v_revenue_at_risk"
        ),
    }


# ============================================================
# CUSTOMER LOOKUP
# ============================================================


def get_customer_record(
    customer_id: str,
) -> dict[str, Any] | None:
    """
    Return one Customer 360 record as a dictionary.
    """

    customer_360 = load_analytics_view(
        "v_customer_360"
    )

    if (
        customer_360.empty
        or "customer_id" not in customer_360.columns
    ):
        return None

    record = customer_360[
        customer_360["customer_id"].astype(str)
        == str(customer_id)
    ]

    if record.empty:
        return None

    return cast(
        dict[str, Any],
        record.iloc[0].to_dict(),
    )


def get_customer_risk_record(
    customer_id: str,
) -> dict[str, Any] | None:
    """
    Return customer-level commercial risk information.
    """

    risk = load_analytics_view(
        "v_revenue_at_risk"
    )

    if (
        risk.empty
        or "customer_id" not in risk.columns
    ):
        return None

    record = risk[
        risk["customer_id"].astype(str)
        == str(customer_id)
    ]

    if record.empty:
        return None

    return cast(
        dict[str, Any],
        record.iloc[0].to_dict(),
    )


def get_customer_rfm_record(
    customer_id: str,
) -> dict[str, Any] | None:
    """
    Return customer RFM segmentation information.
    """

    rfm = load_analytics_view(
        "v_customer_rfm"
    )

    if (
        rfm.empty
        or "customer_id" not in rfm.columns
    ):
        return None

    record = rfm[
        rfm["customer_id"].astype(str)
        == str(customer_id)
    ]

    if record.empty:
        return None

    return cast(
        dict[str, Any],
        record.iloc[0].to_dict(),
    )


# ============================================================
# ML ARTIFACT ACCESS
# ============================================================


def _require_artifact(
    path: Path,
) -> Path:
    """
    Validate that an expected ML artifact exists.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Required ML artifact was not found: {path}. "
            "Run the ML training/scoring pipeline first."
        )

    return path


@st.cache_data(ttl=300, show_spinner=False)
def load_current_churn_scores() -> pd.DataFrame:
    """
    Load latest production customer churn scores.
    """

    path = _require_artifact(
        CURRENT_CHURN_SCORES_PATH
    )

    return pd.read_csv(path)


@st.cache_data(ttl=300, show_spinner=False)
def load_current_churn_summary() -> dict[str, Any]:
    """
    Load latest current-scoring portfolio summary.
    """

    path = _require_artifact(
        CURRENT_CHURN_SUMMARY_PATH
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return cast(
            dict[str, Any],
            json.load(handle),
        )


@st.cache_data(ttl=300, show_spinner=False)
def load_historical_model_metrics() -> dict[str, Any]:
    """
    Load historical validation and untouched-test metrics.
    """

    path = _require_artifact(
        HISTORICAL_MODEL_METRICS_PATH
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return cast(
            dict[str, Any],
            json.load(handle),
        )


@st.cache_data(ttl=300, show_spinner=False)
def load_historical_feature_importance() -> pd.DataFrame:
    """
    Load model feature-importance / coefficient-magnitude output.
    """

    path = _require_artifact(
        HISTORICAL_FEATURE_IMPORTANCE_PATH
    )

    return pd.read_csv(path)


def load_ml_bundle() -> dict[str, Any]:
    """
    Load the complete Machine Learning Intelligence bundle.
    """

    return {
        "scores": load_current_churn_scores(),
        "summary": load_current_churn_summary(),
        "metrics": load_historical_model_metrics(),
        "importance": load_historical_feature_importance(),
    }


def get_ml_customer_record(
    customer_id: str,
) -> dict[str, Any] | None:
    """
    Return the latest predictive churn record for one customer.
    """

    scores = load_current_churn_scores()

    if (
        scores.empty
        or "customer_id" not in scores.columns
    ):
        return None

    record = scores[
        scores["customer_id"].astype(str)
        == str(customer_id)
    ]

    if record.empty:
        return None

    return cast(
        dict[str, Any],
        record.iloc[0].to_dict(),
    )