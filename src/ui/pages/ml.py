from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.components.insight import (
    render_chart_guide,
    render_metric_dictionary,
)
from src.ui.components.ml import (
    clean_feature_name,
    confusion_matrix_frame,
    format_currency,
    format_number,
    format_percent,
    format_ratio_as_percent,
    render_ml_customer_profile,
)
from src.ui.data_service import load_ml_bundle
from src.ui.theme import render_page_header


# ============================================================
# HELPERS
# ============================================================


def _apply_plotly_layout(
    figure,
    height: int = 420,
):
    figure.update_layout(
        height=height,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#CBD5E1",
        ),
        legend_title_text="",
    )

    return figure


def _metric(
    data: dict[str, Any],
    key: str,
    default: float = 0.0,
) -> float:
    try:
        return float(
            data.get(
                key,
                default,
            )
        )
    except (TypeError, ValueError):
        return default


# ============================================================
# PAGE
# ============================================================


def render() -> None:
    """
    Nexus360 Machine Learning Intelligence dashboard.
    """

    render_page_header(
        title="Machine Learning Intelligence",
        subtitle=(
            "Historically validated customer churn prediction, "
            "current portfolio risk, model diagnostics and "
            "customer-level predictive intelligence."
        ),
        eyebrow="NEXUS 360 • PREDICTIVE ML",
    )

    st.info(
        """
**What this page answers:**  
How well does the churn model separate higher-risk customers,
which customers currently require attention, how much contract
value is probability-weighted at risk, and which model signals
matter most?
        """
    )

    try:
        with st.spinner(
            "Loading predictive intelligence..."
        ):
            data = load_ml_bundle()

    except FileNotFoundError as exc:
        st.error(
            str(exc)
        )

        st.code(
            "python -m scripts.run_ml\n"
            "python -m scripts.predict_current_churn"
        )

        return

    scores = data["scores"].copy()
    summary = data["summary"]
    metrics = data["metrics"]
    importance = data["importance"].copy()

    validation = metrics.get(
        "validation",
        {},
    )

    test = metrics.get(
        "test",
        {},
    )

    candidates = pd.DataFrame(
        metrics.get(
            "candidate_models",
            [],
        )
    )

    # ========================================================
    # MODEL STATUS
    # ========================================================

    st.markdown(
        "## 1. Production Model"
    )

    model_columns = st.columns(5)

    model_columns[0].metric(
        "Selected Model",
        str(
            summary.get(
                "selected_model",
                "N/A",
            )
        )
        .replace(
            "_",
            " ",
        )
        .title(),
    )

    model_columns[1].metric(
        "Decision Threshold",
        format_ratio_as_percent(
            summary.get(
                "decision_threshold"
            )
        ),
    )

    model_columns[2].metric(
        "Training Cutoff",
        str(
            summary.get(
                "model_training_cutoff",
                "N/A",
            )
        ),
    )

    model_columns[3].metric(
        "Historical Prediction End",
        str(
            summary.get(
                "model_prediction_end",
                "N/A",
            )
        ),
    )

    model_columns[4].metric(
        "Current Scoring Cutoff",
        str(
            summary.get(
                "scoring_cutoff",
                "N/A",
            )
        ),
    )

    st.caption(
        "The historical model was trained and validated using "
        "point-in-time information available before the training "
        "cutoff. The current scoring snapshot applies the validated "
        "feature schema to the latest eligible customer population."
    )

    # ========================================================
    # CURRENT PORTFOLIO
    # ========================================================

    st.markdown(
        "## 2. Current Churn Risk Portfolio"
    )

    portfolio_columns = st.columns(5)

    portfolio_columns[0].metric(
        "Customers Scored",
        format_number(
            summary.get(
                "customers_scored"
            )
        ),
    )

    portfolio_columns[1].metric(
        "Predicted Churn",
        format_number(
            summary.get(
                "predicted_churn_customers"
            )
        ),
    )

    portfolio_columns[2].metric(
        "Predicted Churn Rate",
        format_percent(
            summary.get(
                "predicted_churn_rate_pct"
            )
        ),
    )

    portfolio_columns[3].metric(
        "Average Churn Probability",
        format_percent(
            summary.get(
                "average_churn_probability_pct"
            )
        ),
    )

    portfolio_columns[4].metric(
        "Expected Contract Value at Risk",
        format_currency(
            summary.get(
                "expected_contract_value_at_risk_usd"
            )
        ),
    )

    render_chart_guide(
        title="How to read the portfolio KPIs",
        definition=(
            "The latest model-scored customer population and the "
            "commercial exposure associated with estimated churn risk."
        ),
        business_question=(
            "Which customers are currently above the decision threshold, "
            "what is the portfolio's overall churn risk, and how much "
            "contract value is exposed to that risk?"
        ),
        interpretation=[
            "Predicted Churn counts customers above the production decision threshold.",
            "Average Churn Probability summarizes the portfolio's model-estimated risk.",
            "Expected Contract Value at Risk weights each customer's active contract value by that customer's churn probability.",
        ],
        business_use=[
            "Use probability for prioritization, then combine it with contract value, customer context and account knowledge before taking retention action.",
        ],
        caveat=(
            "Predicted churn is a model classification, not a confirmed future cancellation. Expected contract value at risk is a probability-weighted exposure estimate, not guaranteed loss."
        ),
    )

    st.warning(
        "Predicted churn is a model classification, not a confirmed "
        "future cancellation. Expected contract value at risk is a "
        "probability-weighted exposure estimate, not guaranteed loss."
    )

    # ========================================================
    # RISK DISTRIBUTION
    # ========================================================

    left, right = st.columns(2)

    with left:

        st.markdown(
            "### Risk Band Distribution"
        )

        risk_order = [
            "Critical",
            "High",
            "Medium",
            "Low",
        ]

        risk_counts = (
            scores["risk_band"]
            .value_counts()
            .reindex(
                risk_order,
                fill_value=0,
            )
            .rename_axis(
                "risk_band"
            )
            .reset_index(
                name="customers"
            )
        )

        figure = px.bar(
            risk_counts,
            x="risk_band",
            y="customers",
            text="customers",
            labels={
                "risk_band": "Risk Band",
                "customers": "Customers",
            },
        )

        figure = _apply_plotly_layout(
            figure
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

        render_chart_guide(
            title="What the risk bands mean",
            definition=(
                "How the currently scored customer population is "
                "distributed across the production risk categories."
            ),
            business_question=(
                "How should the portfolio be prioritized operationally "
                "across critical, high, medium and low churn-risk segments?"
            ),
            interpretation=[
                "Critical customers represent the highest-priority probability tier.",
                "High and Medium indicate decreasing levels of modeled churn risk.",
                "Low represents the lowest-risk group.",
            ],
            business_use=[
                "Start retention review with Critical customers, but also consider contract value and strategic importance.",
            ],
        )

    with right:

        st.markdown(
            "### Churn Probability Distribution"
        )

        figure = px.histogram(
            scores,
            x="churn_probability_pct",
            nbins=20,
            labels={
                "churn_probability_pct": (
                    "Churn Probability (%)"
                ),
            },
        )

        threshold_pct = (
            _metric(
                summary,
                "decision_threshold",
            )
            * 100
        )

        figure.add_vline(
            x=threshold_pct,
            line_dash="dash",
            annotation_text=(
                f"Decision threshold "
                f"{threshold_pct:.0f}%"
            ),
        )

        figure = _apply_plotly_layout(
            figure
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

        render_chart_guide(
            title="How to read churn probability",
            definition=(
                "The distribution of model-estimated churn probability "
                "across currently eligible customers."
            ),
            business_question=(
                "How spread out is the portfolio's churn risk, and where "
                "does the current decision threshold sit relative to that distribution?"
            ),
            interpretation=[
                "Customers farther to the right have higher estimated risk.",
                "The vertical threshold marks the probability level used to convert probability into the production binary churn classification.",
                "The histogram shows whether risk is concentrated in a small tail or broadly distributed across customers.",
            ],
            business_use=[
                "Use the continuous probability for ranking rather than treating every customer above the threshold as equally risky.",
            ],
        )

    # ========================================================
    # FINANCIAL EXPOSURE
    # ========================================================

    st.markdown(
        "## 3. Commercial Exposure"
    )

    exposure = (
        scores.groupby(
            "risk_band",
            as_index=False,
        )
        .agg(
            customers=(
                "customer_id",
                "count",
            ),
            contract_value=(
                "contract_value_in_force_at_cutoff",
                "sum",
            ),
            expected_value_at_risk=(
                "expected_contract_value_at_risk_usd",
                "sum",
            ),
        )
    )

    exposure["risk_band"] = pd.Categorical(
        exposure["risk_band"],
        categories=[
            "Critical",
            "High",
            "Medium",
            "Low",
        ],
        ordered=True,
    )

    exposure = exposure.sort_values(
        "risk_band"
    )

    figure = px.bar(
        exposure,
        x="risk_band",
        y="expected_value_at_risk",
        text_auto=True,
        labels={
            "risk_band": "Risk Band",
            "expected_value_at_risk": (
                "Expected Contract Value at Risk (USD)"
            ),
        },
    )

    figure = _apply_plotly_layout(
        figure
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )

    render_chart_guide(
        title="Expected contract value at risk",
        definition=(
            "Probability-weighted contract exposure aggregated by "
            "customer risk band."
        ),
        business_question=(
            "Where is the largest commercial exposure concentrated within "
            "the scored customer portfolio?"
        ),
        interpretation=[
            "For each customer, active contract value is multiplied by estimated churn probability.",
            "The chart then aggregates those expected-value exposures by risk band.",
            "Customer counts alone can hide where the largest commercial exposure sits.",
        ],
        business_use=[
            "Prioritize accounts where high probability overlaps with meaningful contract value.",
        ],
    )

    # ========================================================
    # TOP RISK CUSTOMERS
    # ========================================================

    st.markdown(
        "## 4. Highest-Priority Customers"
    )

    top_n = st.slider(
        "Customers to display",
        min_value=10,
        max_value=100,
        value=25,
        step=5,
    )

    display_columns = [
        "risk_rank",
        "customer_id",
        "customer_name",
        "customer_segment",
        "industry",
        "churn_probability_pct",
        "risk_band",
        "contract_value_in_force_at_cutoff",
        "expected_contract_value_at_risk_usd",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in scores.columns
    ]

    top_risk = (
        scores.sort_values(
            "risk_rank"
        )
        .head(
            top_n
        )[
            available_columns
        ]
        .copy()
    )

    st.dataframe(
        top_risk,
        width="stretch",
        hide_index=True,
        column_config={
            "risk_rank": "Risk Rank",
            "customer_id": "Customer ID",
            "customer_name": "Customer",
            "customer_segment": "Segment",
            "industry": "Industry",
            "churn_probability_pct": st.column_config.NumberColumn(
                "Churn Probability",
                format="%.2f%%",
            ),
            "risk_band": "Risk Band",
            "contract_value_in_force_at_cutoff": (
                st.column_config.NumberColumn(
                    "Contract Value",
                    format="$%.2f",
                )
            ),
            "expected_contract_value_at_risk_usd": (
                st.column_config.NumberColumn(
                    "Expected Value at Risk",
                    format="$%.2f",
                )
            ),
        },
    )

    # ========================================================
    # CUSTOMER EXPLORER
    # ========================================================

    st.markdown(
        "## 5. Customer Risk Explorer"
    )

    customer_options = scores[
        [
            "customer_id",
            "customer_name",
        ]
    ].copy()

    customer_options["label"] = (
        customer_options["customer_name"].astype(str)
        + " — "
        + customer_options["customer_id"].astype(str)
    )

    selected_label = st.selectbox(
        "Select a scored customer",
        options=customer_options[
            "label"
        ].tolist(),
    )

    selected_row = customer_options[
        customer_options["label"]
        == selected_label
    ].iloc[0]

    selected_customer_id = str(
        selected_row[
            "customer_id"
        ]
    )

    selected_customer = (
        scores[
            scores["customer_id"].astype(str)
            == selected_customer_id
        ]
        .iloc[0]
        .to_dict()
    )

    render_ml_customer_profile(
        selected_customer
    )

    # ========================================================
    # MODEL VALIDATION
    # ========================================================

    st.markdown(
        "## 6. Historical Model Validation"
    )

    st.caption(
        "The following metrics come from historical labeled data. "
        "The test metrics are the primary out-of-sample performance "
        "check shown on this dashboard."
    )

    validation_columns = st.columns(6)

    validation_columns[0].metric(
        "Test ROC-AUC",
        format_number(
            test.get(
                "roc_auc"
            ),
            3,
        ),
    )

    validation_columns[1].metric(
        "Test PR-AUC",
        format_number(
            test.get(
                "pr_auc"
            ),
            3,
        ),
    )

    validation_columns[2].metric(
        "Precision",
        format_ratio_as_percent(
            test.get(
                "precision"
            )
        ),
    )

    validation_columns[3].metric(
        "Recall",
        format_ratio_as_percent(
            test.get(
                "recall"
            )
        ),
    )

    validation_columns[4].metric(
        "F1",
        format_number(
            test.get(
                "f1"
            ),
            3,
        ),
    )

    validation_columns[5].metric(
        "Accuracy",
        format_ratio_as_percent(
            test.get(
                "accuracy"
            )
        ),
    )

    render_chart_guide(
        title="Why multiple ML metrics are shown",
        definition=(
            "The model's discrimination and classification performance "
            "on historical customers whose outcomes are known."
        ),
        business_question=(
            "How well does the model rank churners above non-churners, "
            "and how often does it make correct churn predictions?"
        ),
        interpretation=[
            "ROC-AUC measures ranking ability across thresholds.",
            "PR-AUC focuses on the positive churn class.",
            "Precision asks how many predicted churners actually churned.",
            "Recall asks how many actual churners the model captured.",
            "F1 balances precision and recall.",
        ],
        business_use=[
            "Use the full metric set when deciding whether the model is suitable for prioritization and intervention.",
        ],
    )

    # ========================================================
    # CANDIDATE MODELS
    # ========================================================

    st.markdown(
        "### Candidate Model Comparison"
    )

    if not candidates.empty:

        candidate_display = candidates[
            [
                column
                for column in [
                    "model_name",
                    "threshold",
                    "roc_auc",
                    "pr_auc",
                    "precision",
                    "recall",
                    "f1",
                    "accuracy",
                ]
                if column in candidates.columns
            ]
        ].copy()

        candidate_display["model_name"] = (
            candidate_display[
                "model_name"
            ]
            .astype(str)
            .str.replace(
                "_",
                " ",
                regex=False,
            )
            .str.title()
        )

        st.dataframe(
            candidate_display,
            width="stretch",
            hide_index=True,
        )

        chart_data = candidates.copy()

        chart_data["model_name"] = (
            chart_data[
                "model_name"
            ]
            .astype(str)
            .str.replace(
                "_",
                " ",
                regex=False,
            )
            .str.title()
        )

        chart_data = chart_data.melt(
            id_vars=[
                "model_name",
            ],
            value_vars=[
                "roc_auc",
                "pr_auc",
                "f1",
            ],
            var_name="metric",
            value_name="score",
        )

        figure = px.bar(
            chart_data,
            x="model_name",
            y="score",
            color="metric",
            barmode="group",
            labels={
                "model_name": "Candidate Model",
                "score": "Validation Score",
                "metric": "Metric",
            },
        )

        figure = _apply_plotly_layout(
            figure
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

    st.caption(
        "Model selection uses validation performance and the configured "
        "selection objective. The untouched test set is not used to "
        "choose the winning model."
    )

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    st.markdown(
        "### Untouched Test Confusion Matrix"
    )

    confusion = confusion_matrix_frame(
        test
    )

    st.dataframe(
        confusion,
        width="stretch",
        hide_index=True,
    )

    confusion_columns = st.columns(4)

    confusion_columns[0].metric(
        "True Negatives",
        format_number(
            test.get(
                "tn"
            )
        ),
    )

    confusion_columns[1].metric(
        "False Positives",
        format_number(
            test.get(
                "fp"
            )
        ),
    )

    confusion_columns[2].metric(
        "False Negatives",
        format_number(
            test.get(
                "fn"
            )
        ),
    )

    confusion_columns[3].metric(
        "True Positives",
        format_number(
            test.get(
                "tp"
            )
        ),
    )

    st.info(
        """
**Business interpretation**

- **True Positive:** customer was flagged and actually churned.
- **False Positive:** customer was flagged but did not churn.
- **False Negative:** customer churned but the model did not flag them.
- **True Negative:** customer was not flagged and remained retained.

For retention use cases, false negatives matter because they represent
churn events that the intervention process may fail to surface.
        """
    )

    # ========================================================
    # FEATURE IMPORTANCE
    # ========================================================

    st.markdown(
        "## 7. Model Explainability"
    )

    if not importance.empty:

        top_importance = (
            importance.sort_values(
                "importance_rank"
            )
            .head(
                20
            )
            .copy()
        )

        top_importance[
            "feature_label"
        ] = top_importance[
            "feature"
        ].map(
            clean_feature_name
        )

        top_importance = (
            top_importance.sort_values(
                "importance",
                ascending=True,
            )
        )

        figure = px.bar(
            top_importance,
            x="importance",
            y="feature_label",
            orientation="h",
            labels={
                "importance": (
                    "Importance Magnitude"
                ),
                "feature_label": (
                    "Model Feature"
                ),
            },
        )

        figure = _apply_plotly_layout(
            figure,
            height=650,
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

        render_chart_guide(
            title="How to interpret feature importance",
            definition=(
                "Which transformed model inputs have the largest "
                "importance magnitudes in the selected model."
            ),
            business_question=(
                "Which features most influence the model's ranking "
                "behavior across the customer population?"
            ),
            interpretation=[
                "Longer bars indicate stronger model influence by magnitude.",
                "Categorical features may appear as individual encoded categories.",
                "Importance indicates relative influence rather than a causal effect.",
            ],
            business_use=[
                "Use importance to understand global model behavior, not as proof that a feature causes churn.",
            ],
        )

        st.warning(
            "Feature importance describes model influence or coefficient "
            "magnitude. It does not establish causal relationships, and "
            "magnitude alone does not show whether a feature increases "
            "or decreases churn probability."
        )

    # ========================================================
    # METRIC DICTIONARY
    # ========================================================

    st.markdown(
        "## 8. ML Metric Dictionary"
    )

    render_metric_dictionary(
        [
            {
                "metric": "Churn Probability",
                "definition": (
                    "The model-estimated probability that a customer "
                    "belongs to the churn outcome class."
                ),
            },
            {
                "metric": "Decision Threshold",
                "definition": (
                    "Probability cutoff used to convert continuous churn "
                    "probability into a binary churn prediction."
                ),
            },
            {
                "metric": "Predicted Churn Rate",
                "definition": (
                    "Share of currently scored customers whose probability "
                    "meets or exceeds the production classification threshold."
                ),
            },
            {
                "metric": "Risk Band",
                "definition": (
                    "Operational category used to prioritize customers by "
                    "model-estimated churn risk."
                ),
            },
            {
                "metric": "ROC-AUC",
                "definition": (
                    "Measures how well the model ranks churners above "
                    "non-churners across classification thresholds. Higher is better."
                ),
            },
            {
                "metric": "PR-AUC",
                "definition": (
                    "Area under the precision-recall curve. Particularly "
                    "useful when the churn class is relatively uncommon."
                ),
            },
            {
                "metric": "Precision",
                "definition": (
                    "Among customers predicted to churn, the proportion "
                    "that actually churned in historical evaluation."
                ),
            },
            {
                "metric": "Recall",
                "definition": (
                    "Among customers that actually churned, the proportion "
                    "successfully identified by the model."
                ),
            },
            {
                "metric": "F1 Score",
                "definition": (
                    "Harmonic mean of precision and recall. It summarizes "
                    "the balance between the two."
                ),
            },
            {
                "metric": "Accuracy",
                "definition": (
                    "Share of all classifications that were correct. "
                    "Accuracy should not be interpreted alone for an "
                    "imbalanced churn problem."
                ),
            },
            {
                "metric": "Expected Contract Value at Risk",
                "definition": (
                    "Active contract value multiplied by estimated churn "
                    "probability. This is probability-weighted exposure, "
                    "not guaranteed lost revenue."
                ),
            },
            {
                "metric": "Feature Importance",
                "definition": (
                    "Relative magnitude of a model input's influence in "
                    "the selected model. Importance does not imply causality."
                ),
            },
        ]
    )

    # ========================================================
    # GOVERNANCE
    # ========================================================

    st.markdown(
        "## 9. Model Governance Notes"
    )

    st.markdown(
        f"""
- **Historical training cutoff:** `{summary.get('model_training_cutoff', 'N/A')}`
- **Historical outcome window end:** `{summary.get('model_prediction_end', 'N/A')}`
- **Current scoring cutoff:** `{summary.get('scoring_cutoff', 'N/A')}`
- **Selected model:** `{summary.get('selected_model', 'N/A')}`
- **Production threshold:** `{summary.get('decision_threshold', 'N/A')}`
- **Current customers scored:** `{summary.get('customers_scored', 'N/A')}`

The model should be used as a **decision-support and prioritization
tool**. Customer intervention decisions should combine model output
with account context, contractual information and human review.

Current scores can also change when the underlying customer snapshot
or model artifacts are regenerated.
        """
    )