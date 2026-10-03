from __future__ import annotations

import html
from textwrap import dedent

import streamlit as st


def _format_currency(
    value: float | int | None,
) -> str:
    """
    Format numeric values as compact USD currency.
    """

    if value is None:
        return "$0"

    numeric_value = float(value)

    absolute = abs(numeric_value)

    if absolute >= 1_000_000_000:
        return (
            f"${numeric_value / 1_000_000_000:,.2f}B"
        )

    if absolute >= 1_000_000:
        return (
            f"${numeric_value / 1_000_000:,.2f}M"
        )

    if absolute >= 1_000:
        return (
            f"${numeric_value / 1_000:,.1f}K"
        )

    return f"${numeric_value:,.2f}"


def _format_number(
    value: float | int | None,
) -> str:
    """
    Format numeric values using compact enterprise notation.
    """

    if value is None:
        return "0"

    numeric_value = float(value)

    absolute = abs(numeric_value)

    if absolute >= 1_000_000_000:
        return (
            f"{numeric_value / 1_000_000_000:,.2f}B"
        )

    if absolute >= 1_000_000:
        return (
            f"{numeric_value / 1_000_000:,.2f}M"
        )

    if absolute >= 1_000:
        return (
            f"{numeric_value / 1_000:,.1f}K"
        )

    if numeric_value.is_integer():
        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.2f}"


def _format_percent(
    value: float | int | None,
) -> str:
    """
    Format percentage values.

    Nexus360 semantic views already expose percentage metrics
    on the 0-100 scale, therefore values are not multiplied
    by 100 here.
    """

    if value is None:
        return "0.00%"

    return f"{float(value):,.2f}%"


def render_kpi(
    label: str,
    value: float | int | str | None,
    *,
    kind: str = "number",
    detail: str = "",
    sentiment: str = "neutral",
) -> None:
    """
    Render a reusable Nexus360 KPI card.

    Parameters
    ----------
    label:
        KPI title.

    value:
        KPI value.

    kind:
        One of:
        - number
        - currency
        - percent
        - text

    detail:
        Supporting description.

    sentiment:
        One of:
        - positive
        - negative
        - neutral
    """

    # ==========================================================
    # FORMAT VALUE
    # ==========================================================

    if kind == "currency":

        display_value = _format_currency(
            value  # type: ignore[arg-type]
        )

    elif kind == "percent":

        display_value = _format_percent(
            value  # type: ignore[arg-type]
        )

    elif kind == "number":

        display_value = _format_number(
            value  # type: ignore[arg-type]
        )

    elif kind == "text":

        display_value = (
            str(value)
            if value is not None
            else "—"
        )

    else:

        raise ValueError(
            "Unsupported KPI kind. "
            "Expected one of: "
            "'number', 'currency', 'percent', 'text'."
        )

    # ==========================================================
    # SENTIMENT
    # ==========================================================

    sentiment_class = {
        "positive": "nexus-positive",
        "negative": "nexus-negative",
        "neutral": "nexus-neutral",
    }.get(
        sentiment,
        "nexus-neutral",
    )

    # ==========================================================
    # HTML SAFETY
    # ==========================================================

    safe_label = html.escape(
        str(label)
    )

    safe_value = html.escape(
        str(display_value)
    )

    safe_detail = html.escape(
        str(detail)
    )

    # ==========================================================
    # HTML
    #
    # IMPORTANT:
    # Markdown interprets leading indentation as code.
    # dedent(...).strip() prevents Streamlit from displaying
    # our <div> tags literally.
    # ==========================================================

    card_html = f"""
    <div class="nexus-kpi">
        <div class="nexus-kpi-label">{safe_label}</div>
        <div class="nexus-kpi-value">{safe_value}</div>
        <div class="nexus-kpi-detail {sentiment_class}">{safe_detail}</div>
    </div>
    """

    st.markdown(
        dedent(card_html).strip(),
        unsafe_allow_html=True,
    )