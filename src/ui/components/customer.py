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
    """
    Human-readable USD formatting.
    """

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
) -> str:

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if pd.isna(numeric):
        return "N/A"

    return f"{numeric:,.2f}%"


def format_boolean(
    value: Any,
) -> str:

    if value is True:
        return "Yes"

    if value is False:
        return "No"

    return "N/A"


# ============================================================
# CUSTOMER PROFILE
# ============================================================


def render_customer_identity(
    customer: dict[str, Any],
) -> None:
    """
    Render the identity/profile section of a selected customer.
    """

    customer_name = customer.get(
        "customer_name",
        "Unknown Customer",
    )

    customer_id = customer.get(
        "customer_id",
        "N/A",
    )

    st.markdown(
        f"### {customer_name}"
    )

    st.caption(
        f"Customer ID: {customer_id}"
    )

    columns = st.columns(4)

    columns[0].metric(
        "Segment",
        str(
            customer.get(
                "customer_segment",
                "N/A",
            )
        ),
    )

    columns[1].metric(
        "Industry",
        str(
            customer.get(
                "industry",
                "N/A",
            )
        ),
    )

    columns[2].metric(
        "Status",
        str(
            customer.get(
                "customer_status",
                "N/A",
            )
        ),
    )

    columns[3].metric(
        "AI Customer",
        format_boolean(
            customer.get(
                "is_ai_customer"
            )
        ),
    )

    with st.expander(
        "Customer profile details",
        expanded=False,
    ):

        profile = {
            "Employee Band": customer.get(
                "employee_band",
                "N/A",
            ),
            "Annual Revenue Band": customer.get(
                "annual_revenue_band",
                "N/A",
            ),
            "Acquisition Channel": customer.get(
                "acquisition_channel",
                "N/A",
            ),
            "Signup Date": customer.get(
                "signup_date",
                "N/A",
            ),
        }

        profile_df = pd.DataFrame(
            profile.items(),
            columns=[
                "Attribute",
                "Value",
            ],
        )

        st.dataframe(
            profile_df,
            width="stretch",
            hide_index=True,
        )


# ============================================================
# COMMERCIAL VALUE
# ============================================================


def render_customer_commercial_value(
    customer: dict[str, Any],
) -> None:

    st.markdown(
        "#### Commercial Value"
    )

    columns = st.columns(4)

    columns[0].metric(
        "Lifetime Revenue",
        format_currency(
            customer.get(
                "lifetime_revenue_usd"
            )
        ),
    )

    columns[1].metric(
        "Lifetime Gross Profit",
        format_currency(
            customer.get(
                "lifetime_gross_profit_usd"
            )
        ),
    )

    columns[2].metric(
        "Transactions",
        format_number(
            customer.get(
                "transactions"
            )
        ),
    )

    columns[3].metric(
        "Products Purchased",
        format_number(
            customer.get(
                "purchased_products"
            )
        ),
    )


# ============================================================
# SUBSCRIPTION VALUE
# ============================================================


def render_customer_subscription(
    customer: dict[str, Any],
) -> None:

    st.markdown(
        "#### Subscription Footprint"
    )

    columns = st.columns(3)

    columns[0].metric(
        "Subscriptions",
        format_number(
            customer.get(
                "subscriptions"
            )
        ),
    )

    columns[1].metric(
        "Active Subscriptions",
        format_number(
            customer.get(
                "active_subscriptions"
            )
        ),
    )

    columns[2].metric(
        "Active Contract Value",
        format_currency(
            customer.get(
                "active_contract_value_usd"
            )
        ),
    )


# ============================================================
# SUPPORT EXPERIENCE
# ============================================================


def render_customer_support(
    customer: dict[str, Any],
) -> None:

    st.markdown(
        "#### Support Experience"
    )

    columns = st.columns(5)

    columns[0].metric(
        "Support Tickets",
        format_number(
            customer.get(
                "support_tickets"
            )
        ),
    )

    columns[1].metric(
        "SLA Breaches",
        format_number(
            customer.get(
                "sla_breaches"
            )
        ),
    )

    columns[2].metric(
        "Reopened Tickets",
        format_number(
            customer.get(
                "reopened_tickets"
            )
        ),
    )

    columns[3].metric(
        "Avg Resolution",
        (
            f"{format_number(customer.get('avg_resolution_hours'), 1)} hrs"
        ),
    )

    columns[4].metric(
        "Customer Satisfaction",
        format_number(
            customer.get(
                "avg_customer_satisfaction"
            ),
            2,
        ),
    )


# ============================================================
# CLOUD ENGAGEMENT
# ============================================================


def render_customer_cloud(
    customer: dict[str, Any],
) -> None:

    st.markdown(
        "#### Cloud & AI Engagement"
    )

    row_one = st.columns(4)

    row_one[0].metric(
        "Compute Hours",
        format_number(
            customer.get(
                "compute_hours"
            ),
            1,
        ),
    )

    row_one[1].metric(
        "Storage GB",
        format_number(
            customer.get(
                "storage_gb"
            ),
            1,
        ),
    )

    row_one[2].metric(
        "Network GB",
        format_number(
            customer.get(
                "network_gb"
            ),
            1,
        ),
    )

    row_one[3].metric(
        "AI Tokens (M)",
        format_number(
            customer.get(
                "ai_tokens_million"
            ),
            2,
        ),
    )

    row_two = st.columns(4)

    row_two[0].metric(
        "API Requests",
        format_number(
            customer.get(
                "requests_count"
            )
        ),
    )

    row_two[1].metric(
        "Failed Requests",
        format_number(
            customer.get(
                "failed_requests"
            )
        ),
    )

    row_two[2].metric(
        "Failure Rate",
        format_percent(
            customer.get(
                "request_failure_rate_pct"
            )
        ),
    )

    row_two[3].metric(
        "Cloud Cost",
        format_currency(
            customer.get(
                "cloud_cost_usd"
            )
        ),
    )


# ============================================================
# CUSTOMER RISK
# ============================================================


def render_customer_risk(
    risk: dict[str, Any] | None,
    rfm: dict[str, Any] | None,
) -> None:

    st.markdown(
        "#### Customer Risk & Behavioral Signals"
    )

    if risk is None and rfm is None:
        st.info(
            "No additional customer risk or RFM information "
            "is available for this customer."
        )
        return

    columns = st.columns(5)

    if risk:

        columns[0].metric(
            "Composite Risk",
            format_number(
                risk.get(
                    "composite_risk_score"
                ),
                2,
            ),
        )

        columns[1].metric(
            "Revenue at Risk",
            format_currency(
                risk.get(
                    "revenue_at_risk_usd"
                )
            ),
        )

        columns[2].metric(
            "Risk Band",
            str(
                risk.get(
                    "revenue_risk_band",
                    "N/A",
                )
            ),
        )

    if rfm:

        columns[3].metric(
            "RFM Score",
            format_number(
                rfm.get(
                    "rfm_total_score"
                )
            ),
        )

        columns[4].metric(
            "RFM Segment",
            str(
                rfm.get(
                    "rfm_segment",
                    "N/A",
                )
            ),
        )

    st.caption(
        "Revenue at Risk is an analytical exposure estimate. "
        "It is not a statement that the customer will churn or "
        "that the revenue will definitely be lost."
    )