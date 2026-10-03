from __future__ import annotations

import streamlit as st

from src.ai.config import get_ai_config
from src.ai.copilot import NexusCopilot
from src.ui.components.ai import (
    process_copilot_question,
    render_ai_status,
    render_chat_history,
    render_context_info,
    render_suggested_questions,
)
from src.ui.theme import render_page_header


# ============================================================
# SESSION STATE
# ============================================================


def _initialize_state() -> None:

    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    if "ai_context" not in st.session_state:
        st.session_state.ai_context = "ml"

    if "ai_last_model" not in st.session_state:
        st.session_state.ai_last_model = None


# ============================================================
# COPILOT
# ============================================================


@st.cache_resource(show_spinner=False)
def _get_copilot() -> NexusCopilot:
    """
    Create one Gemini Copilot client per Streamlit runtime.
    """

    return NexusCopilot()


# ============================================================
# PAGE
# ============================================================


def render() -> None:
    """
    Render Nexus360 AI Copilot.
    """

    _initialize_state()

    config = get_ai_config()

    render_page_header(
        title="Nexus360 AI Copilot",
        subtitle=(
            "Grounded conversational intelligence across "
            "enterprise analytics and predictive risk."
        ),
        eyebrow=(
            "NEXUS 360 • GENERATIVE AI"
        ),
    )

    st.info(
        """
**What this page does:**  
Nexus360 Copilot converts approved analytical context into
business explanations, evidence-based interpretations and
recommended actions.

The model does **not** receive unrestricted database access.
        """
    )

    # ========================================================
    # CONFIGURATION CHECK
    # ========================================================

    if not config.is_configured:

        st.error(
            "Gemini is not configured. "
            "Set GEMINI_API_KEY before using the Copilot."
        )

        return

    # ========================================================
    # CONTEXT CONTROL
    # ========================================================

    control_col1, control_col2 = st.columns(
        [3, 1]
    )

    with control_col1:

        selected_label = st.segmented_control(
            "Analytical Context",
            options=[
                "Predictive ML",
                "Executive",
            ],
            default=(
                "Predictive ML"
                if st.session_state.ai_context == "ml"
                else "Executive"
            ),
            width="stretch",
        )

    selected_context = (
        "executive"
        if selected_label == "Executive"
        else "ml"
    )

    # Clear conversation when context changes because previous
    # answers were grounded in a different analytical dataset.

    if (
        selected_context
        != st.session_state.ai_context
    ):

        st.session_state.ai_context = (
            selected_context
        )

        st.session_state.ai_messages = []

        st.rerun()

    with control_col2:

        st.write("")

        if st.button(
            "Clear conversation",
            width="stretch",
        ):

            st.session_state.ai_messages = []

            st.rerun()

    context = st.session_state.ai_context

    # ========================================================
    # STATUS
    # ========================================================

    render_ai_status(
        model_name=(
            st.session_state.ai_last_model
            or config.model_name
        ),
        grounded=True,
    )

    render_context_info(
        context
    )

    st.divider()

    # ========================================================
    # SUGGESTIONS
    # ========================================================

    suggested_question = (
        render_suggested_questions(
            context
        )
    )

    st.divider()

    # ========================================================
    # CHAT HISTORY
    # ========================================================

    if not st.session_state.ai_messages:

        with st.chat_message(
            "assistant"
        ):

            if context == "ml":

                st.markdown(
                    """
### Predictive intelligence ready

I can explain the current churn-risk portfolio,
historical model performance, risk drivers and
customer-level priorities.

Try asking:

**“Which customers need immediate retention attention?”**
                    """
                )

            else:

                st.markdown(
                    """
### Executive intelligence ready

I can explain enterprise KPIs, revenue performance,
product leadership, regional performance and
commercial exposure using the approved Executive
Command Center context.

Try asking:

**“What should an executive focus on right now?”**
                    """
                )

    render_chat_history(
        st.session_state.ai_messages
    )

    # ========================================================
    # COPILOT REQUEST
    # ========================================================

    user_question = st.chat_input(
        "Ask Nexus360 about your analytics..."
    )

    question = (
        suggested_question
        or user_question
    )

    if question:

        copilot = _get_copilot()

        process_copilot_question(
            question=question,
            page=context,
            ask_function=copilot.ask,
        )

        st.rerun()

    # ========================================================
    # EXPLANATION
    # ========================================================

    st.divider()

    with st.expander(
        "How Nexus360 Copilot works"
    ):

        st.markdown(
            """
### Grounded AI architecture

The Copilot follows a controlled analytical pipeline:

`Question → Guardrails → Approved Analytics Context → Gemini → Grounded Response`

**Guardrails**  
Unsafe database-modification instructions and requests for
credentials or secrets are rejected before model generation.

**Approved context**  
The model receives curated Nexus360 analytical facts rather
than unrestricted warehouse access.

**Grounding**  
Gemini is instructed not to invent unsupported metrics,
customers, financial values or model results.

**Predictive interpretation**  
Churn probabilities represent statistical estimates rather
than guaranteed customer outcomes.

**Decision support**  
Recommendations are analytical suggestions intended to help
users investigate and prioritize business actions.
            """
        )

    with st.expander(
        "AI interpretation guidance"
    ):

        st.markdown(
            """
**Churn Probability**  
Estimated likelihood associated with the modeled churn
outcome.

**Decision Threshold**  
Probability level used to convert a score into a binary
prediction.

**ROC-AUC**  
Measures the model's ability to rank churned customers above
retained customers across classification thresholds.

**PR-AUC**  
Precision-recall performance, especially useful for
imbalanced churn datasets.

**Precision**  
Of customers predicted to churn, the historical proportion
that actually churned.

**Recall**  
Of customers that actually churned, the historical proportion
identified by the model.

AI explanations should be interpreted together with these
model-performance measures rather than treating predictions
as certainty.
            """
        )