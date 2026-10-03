from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# FORMATTING
# ============================================================


def format_currency(
    value: Any,
) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if pd.isna(numeric):
        return "N/A"

    absolute = abs(numeric)

    if absolute >= 1_000_000_000:
        return f"${numeric / 1_000_000_000:,.2f}B"

    if absolute >= 1_000_000:
        return f"${numeric / 1_000_000:,.2f}M"

    if absolute >= 1_000:
        return f"${numeric / 1_000:,.2f}K"

    return f"${numeric:,.2f}"


def format_number(
    value: Any,
    decimals: int = 0,
) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if pd.isna(numeric):
        return "N/A"

    return f"{numeric:,.{decimals}f}"


def format_percent(
    value: Any,
    decimals: int = 2,
) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if pd.isna(numeric):
        return "N/A"

    return f"{numeric:,.{decimals}f}%"


def format_ratio_as_percent(
    value: Any,
    decimals: int = 2,
) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if pd.isna(numeric):
        return "N/A"

    return f"{numeric * 100:,.{decimals}f}%"


def clean_feature_name(
    feature: Any,
) -> str:
    """
    Convert transformed sklearn feature names into dashboard labels.
    """

    label = str(feature)

    label = label.replace(
        "numeric__",
        "",
    )

    label = label.replace(
        "categorical__",
        "",
    )

    label = label.replace(
        "_",
        " ",
    )

    return label.strip().title()


# ============================================================
# CUSTOMER RISK CARD
# ============================================================


def render_ml_customer_profile(
    customer: dict[str, Any],
) -> None:
    """
    Render a selected customer's predictive churn profile.
    """

    st.markdown(
        "### Customer Predictive Risk Profile"
    )

    st.markdown(
        f"#### {customer.get('customer_name', 'Unknown Customer')}"
    )

    st.caption(
        f"Customer ID: {customer.get('customer_id', 'N/A')}"
    )

    row_one = st.columns(5)

    row_one[0].metric(
        "Churn Probability",
        format_percent(
            customer.get(
                "churn_probability_pct"
            )
        ),
    )

    row_one[1].metric(
        "Risk Band",
        str(
            customer.get(
                "risk_band",
                "N/A",
            )
        ),
    )

    row_one[2].metric(
        "Risk Rank",
        format_number(
            customer.get(
                "risk_rank"
            )
        ),
    )

    row_one[3].metric(
        "Contract Value",
        format_currency(
            customer.get(
                "contract_value_in_force_at_cutoff"
            )
        ),
    )

    row_one[4].metric(
        "Expected Value at Risk",
        format_currency(
            customer.get(
                "expected_contract_value_at_risk_usd"
            )
        ),
    )

    st.caption(
        "Expected Value at Risk = contract value currently in force "
        "multiplied by estimated churn probability. It is an "
        "expected-value exposure measure, not guaranteed revenue loss."
    )

    st.markdown(
        "#### Customer Context"
    )

    row_two = st.columns(4)

    row_two[0].metric(
        "Segment",
        str(
            customer.get(
                "customer_segment",
                "N/A",
            )
        ),
    )

    row_two[1].metric(
        "Industry",
        str(
            customer.get(
                "industry",
                "N/A",
            )
        ),
    )

    row_two[2].metric(
        "Active Subscriptions",
        format_number(
            customer.get(
                "subscriptions_in_force_at_cutoff"
            )
        ),
    )

    row_two[3].metric(
        "Historical Auto-Renew",
        format_percent(
            customer.get(
                "historical_auto_renew_pct"
            )
        ),
    )

    st.markdown(
        "#### Recent Behavioral Signals"
    )

    row_three = st.columns(5)

    row_three[0].metric(
        "Trailing Revenue",
        format_currency(
            customer.get(
                "trailing_revenue_usd"
            )
        ),
    )

    row_three[1].metric(
        "Transactions",
        format_number(
            customer.get(
                "trailing_transactions"
            )
        ),
    )

    row_three[2].metric(
        "Support Tickets",
        format_number(
            customer.get(
                "trailing_support_tickets"
            )
        ),
    )

    row_three[3].metric(
        "SLA Breach Rate",
        format_percent(
            customer.get(
                "trailing_sla_breach_rate_pct"
            )
        ),
    )

    row_three[4].metric(
        "Request Failure Rate",
        format_percent(
            customer.get(
                "trailing_request_failure_rate_pct"
            )
        ),
    )

    with st.expander(
        "How to interpret this customer score",
        expanded=False,
    ):
        st.markdown(
            """
**Churn Probability**  
The model's estimated probability of churn based on the
customer information available at the scoring cutoff.

**Risk Band**  
A prioritization category derived from model probability and
the production decision framework.

**Risk Rank**  
The customer's position when all scored customers are ordered
from highest to lowest churn probability.

**Contract Value in Force**  
Subscription contract value active at the scoring cutoff.

**Expected Contract Value at Risk**  
Probability-weighted commercial exposure. A customer with a
large contract and moderate probability may still represent
substantial financial exposure.

The model is a decision-support system. A high score does not
prove that a customer will churn.
            """
        )


# ============================================================
# CONFUSION MATRIX
# ============================================================


def confusion_matrix_frame(
    metrics: dict[str, Any],
) -> pd.DataFrame:
    """
    Build a presentation-ready confusion matrix.
    """

    return pd.DataFrame(
        [
            {
                "Actual": "Retained",
                "Predicted Retained": int(
                    metrics.get(
                        "tn",
                        0,
                    )
                ),
                "Predicted Churn": int(
                    metrics.get(
                        "fp",
                        0,
                    )
                ),
            },
            {
                "Actual": "Churned",
                "Predicted Retained": int(
                    metrics.get(
                        "fn",
                        0,
                    )
                ),
                "Predicted Churn": int(
                    metrics.get(
                        "tp",
                        0,
                    )
                ),
            },
        ]
    )