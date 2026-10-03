from __future__ import annotations

import json
from typing import Any

from src.ai.grounding import NexusGroundingEngine
from src.ai.intent_router import NexusIntentRouter
from src.ai.retriever import NexusSemanticRetriever
from src.ai.schemas import AnalyticsContext
from src.ai.semantic_catalog import get_domain


class NexusContextBuilder:
    """
    Enterprise grounding context builder.

    Pipeline:
        question
        -> deterministic intent routing
        -> controlled semantic retrieval
        -> evidence packaging
        -> AnalyticsContext

    Gemini never receives database credentials or unrestricted
    SQL/database access.

    The final AnalyticsContext.page represents the resolved
    analytical domain rather than merely the page from which
    the question originated.
    """

    def __init__(
        self,
        *,
        router: NexusIntentRouter | None = None,
        retriever: NexusSemanticRetriever | None = None,
        grounding: NexusGroundingEngine | None = None,
    ) -> None:

        self.router = (
            router
            or NexusIntentRouter()
        )

        self.retriever = (
            retriever
            or NexusSemanticRetriever()
        )

        self.grounding = (
            grounding
            or NexusGroundingEngine()
        )

    # ========================================================
    # CONTEXT BUILDING
    # ========================================================

    def build(
        self,
        page: str,
        question: str,
    ) -> AnalyticsContext:
        """
        Build grounded analytical context for one question.

        Parameters
        ----------
        page:
            Page from which the question originated. This is
            treated only as routing context / a weak prior.

        question:
            User analytical question.

        Returns
        -------
        AnalyticsContext
            Safe grounded context whose ``page`` is the
            resolved Nexus360 analytical domain.
        """

        requested_page = str(
            page or "general"
        ).strip()

        cleaned_question = str(
            question or ""
        ).strip()

        # ----------------------------------------------------
        # 1. Resolve analytical intent
        # ----------------------------------------------------

        intent = self.router.route(
            cleaned_question,
            page=requested_page,
        )

        resolved_domain = (
            intent.primary_domain
        )

        # ----------------------------------------------------
        # 2. Retrieve only approved semantic evidence
        # ----------------------------------------------------

        retrieval = self.retriever.retrieve(
            resolved_domain
        )

        # ----------------------------------------------------
        # 3. Convert retrieved data into grounded evidence
        # ----------------------------------------------------

        evidence = self.grounding.build(
            retrieval
        )

        # ----------------------------------------------------
        # 4. Resolve semantic-domain metadata
        # ----------------------------------------------------

        domain = get_domain(
            resolved_domain
        )

        metadata = dict(
            evidence.metadata
        )

        metadata.update(
            {
                # Page where the question originated.
                "requested_page": requested_page,

                # Domain selected by deterministic routing.
                "resolved_domain": resolved_domain,

                "resolved_domain_label": (
                    domain.label
                ),

                # Routing diagnostics.
                "intent_confidence": (
                    intent.confidence
                ),

                "matched_terms": list(
                    intent.matched_terms
                ),

                "related_domains": list(
                    intent.related_domains
                ),

                # Security / grounding guarantees.
                "database_access": False,

                "grounding_mode": (
                    "approved_semantic_evidence"
                ),
            }
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # AnalyticsContext.page must represent the RESOLVED
        # analytical domain.
        #
        # requested_page is preserved separately in metadata.
        # ----------------------------------------------------

        return AnalyticsContext(
            page=resolved_domain,
            question=cleaned_question,
            metrics=evidence.metrics,
            insights=evidence.insights,
            definitions=evidence.definitions,
            metadata=metadata,
        )

    # ========================================================
    # PROMPT SERIALIZATION
    # ========================================================

    @staticmethod
    def to_prompt_context(
        context: AnalyticsContext,
    ) -> str:
        """
        Serialize approved grounded context for the LLM.

        Only the already-grounded AnalyticsContext is exposed.
        No database credentials, SQL engine or unrestricted
        retrieval interface is included.
        """

        payload: dict[str, Any] = {
            "page": context.page,
            "question": context.question,
            "metrics": context.metrics,
            "insights": context.insights,
            "definitions": context.definitions,
            "metadata": context.metadata,
        }

        return json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            default=str,
        )