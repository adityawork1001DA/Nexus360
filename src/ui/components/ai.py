from __future__ import annotations

from typing import Callable

import streamlit as st


# ============================================================
# AI STATUS
# ============================================================


def render_ai_status(
    *,
    model_name: str,
    grounded: bool = True,
) -> None:
    """
    Render compact AI runtime information.
    """

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "AI Model",
            model_name,
        )

    with col2:
        st.metric(
            "Grounding",
            "Enabled" if grounded else "Disabled",
        )

    with col3:
        st.metric(
            "Database Access",
            "None",
        )


# ============================================================
# CONTEXT DESCRIPTION
# ============================================================


def render_context_info(
    context: str,
) -> None:
    """
    Explain what information is available to the Copilot.
    """

    descriptions = {
        "executive": (
            "Enterprise KPI, revenue trend, regional performance, "
            "product performance and commercial-risk context."
        ),
        "ml": (
            "Current customer churn scores, risk distribution, "
            "model performance and feature-importance context."
        ),
    }

    description = descriptions.get(
        context,
        "Controlled Nexus360 analytical context.",
    )

    st.info(
        f"**Active analytical context: "
        f"{context.title()}**\n\n"
        f"{description}"
    )


# ============================================================
# SUGGESTED QUESTIONS
# ============================================================


def render_suggested_questions(
    context: str,
) -> str | None:
    """
    Render context-aware example questions.

    Returns the selected question or None.
    """

    questions = {
        "executive": [
            (
                "What are the most important executive "
                "insights right now?"
            ),
            (
                "Which product currently leads revenue?"
            ),
            (
                "Where is the largest commercial risk?"
            ),
            (
                "Explain the overall business performance "
                "in executive language."
            ),
        ],
        "ml": [
            (
                "Which customers currently have the "
                "highest churn risk?"
            ),
            (
                "How reliable is the churn model?"
            ),
            (
                "What factors are associated with "
                "customer churn risk?"
            ),
            (
                "What should management prioritize "
                "based on the churn portfolio?"
            ),
        ],
    }

    available = questions.get(
        context,
        questions["ml"],
    )

    st.caption("SUGGESTED QUESTIONS")

    selected: str | None = None

    columns = st.columns(2)

    for index, question in enumerate(available):

        column = columns[index % 2]

        with column:

            if st.button(
                question,
                key=(
                    f"ai_suggestion_"
                    f"{context}_{index}"
                ),
                width="stretch",
            ):
                selected = question

    return selected


# ============================================================
# CHAT HISTORY
# ============================================================


def render_chat_history(
    messages: list[dict[str, str]],
) -> None:
    """
    Render current Streamlit Copilot conversation.
    """

    for message in messages:

        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        if role not in {
            "user",
            "assistant",
        }:
            continue

        with st.chat_message(role):
            st.markdown(content)


# ============================================================
# ERROR PANEL
# ============================================================


def render_ai_error(
    error: Exception,
) -> None:
    """
    Convert backend AI exceptions into safe UI messages.
    """

    message = str(error)

    if isinstance(error, ValueError):

        st.warning(
            message
        )

        return

    st.error(
        "Nexus360 Copilot could not complete the request. "
        "Please try again."
    )

    with st.expander(
        "Technical details"
    ):
        st.code(message)


# ============================================================
# CHAT EXECUTION
# ============================================================


def process_copilot_question(
    *,
    question: str,
    page: str,
    ask_function: Callable,
) -> bool:
    """
    Execute one Copilot interaction.

    Returns True when a response was successfully generated.
    """

    cleaned = question.strip()

    if not cleaned:
        return False

    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    st.session_state.ai_messages.append(
        {
            "role": "user",
            "content": cleaned,
        }
    )

    try:

        with st.spinner(
            "Nexus360 Copilot is analyzing "
            "the available context..."
        ):

            response = ask_function(
                cleaned,
                page=page,
            )

        st.session_state.ai_messages.append(
            {
                "role": "assistant",
                "content": response.answer,
            }
        )

        st.session_state.ai_last_model = (
            response.model_name
        )

        return True

    except Exception as exc:

        st.session_state.ai_messages.append(
            {
                "role": "assistant",
                "content": (
                    "I could not complete that request. "
                    f"{str(exc)}"
                ),
            }
        )

        render_ai_error(exc)

        return False