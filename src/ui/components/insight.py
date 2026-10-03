from __future__ import annotations

import streamlit as st


def render_chart_guide(
    *,
    title: str,
    definition: str,
    business_question: str,
    interpretation: list[str],
    business_use: list[str] | None = None,
    caveat: str | None = None,
) -> None:
    """
    Render an expandable explanation underneath an analytical
    visualization.

    Keeps dashboards visually clean while allowing recruiters,
    analysts and business users to understand the metric.
    """

    with st.expander(
        f"ⓘ How to interpret — {title}",
        expanded=False,
    ):
        st.markdown("**What it shows**")
        st.write(definition)

        st.markdown("**Business question**")
        st.write(business_question)

        st.markdown("**How to read it**")

        for item in interpretation:
            st.markdown(f"- {item}")

        if business_use:
            st.markdown("**Business use**")

            for item in business_use:
                st.markdown(f"- {item}")

        if caveat:
            st.markdown("**Important caveat**")
            st.info(caveat)


def render_metric_dictionary(
    metrics: list[dict[str, str]],
) -> None:
    """
    Render a metric dictionary.

    Each dictionary entry may contain:
        metric
        definition
        formula
        interpretation
    """

    st.subheader("Metric Dictionary")

    st.caption(
        "Definitions and formulas used across this dashboard."
    )

    for metric in metrics:
        metric_name = metric.get(
            "metric",
            "Metric",
        )

        with st.expander(
            f"ⓘ {metric_name}",
            expanded=False,
        ):
            definition = metric.get("definition")

            if definition:
                st.markdown("**Definition**")
                st.write(definition)

            formula = metric.get("formula")

            if formula:
                st.markdown("**Formula**")
                st.code(
                    formula,
                    language=None,
                )

            interpretation = metric.get(
                "interpretation"
            )

            if interpretation:
                st.markdown("**Interpretation**")
                st.write(interpretation)


def render_insight_panel(
    *,
    metric: str,
    insight: str,
    potential_action: str,
    warning: bool = False,
) -> None:
    """
    Explicitly separate measured facts from analytical
    interpretation and possible business actions.
    """

    if warning:
        container = st.warning
    else:
        container = st.info

    container(
        f"""
**Metric:** {metric}

**Analytical insight:** {insight}

**Potential business action:** {potential_action}
        """
    )