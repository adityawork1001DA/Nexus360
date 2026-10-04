from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.ai.semantic_catalog import get_domain
from src.ui.data_service import (
    load_analytics_view,
    load_ml_bundle,
)


@dataclass
class RetrievalBundle:
    domain: str
    frames: dict[str, pd.DataFrame] = field(
        default_factory=dict
    )
    ml: dict = field(
        default_factory=dict
    )
    errors: list[str] = field(
        default_factory=list
    )


class NexusSemanticRetriever:
    """
    Controlled retrieval layer.

    Only approved Nexus360 semantic views and approved
    ML artifacts can enter the AI grounding pipeline.

    Semantic views are loaded without an artificial row limit
    so aggregate metrics such as counts, sums and averages are
    calculated from the complete analytical dataset.

    The grounding layer remains responsible for restricting
    the number of sample records serialized into the LLM
    context.
    """

    def retrieve(
        self,
        domain: str,
    ) -> RetrievalBundle:

        definition = get_domain(domain)

        result = RetrievalBundle(
            domain=definition.key
        )

        if definition.key == "ml":

            try:
                result.ml = load_ml_bundle()

            except Exception as exc:
                result.errors.append(
                    f"ML retrieval failed: {exc}"
                )

            return result

        for view in definition.views:

            try:
                frame = load_analytics_view(
                    view_name=view,
                    limit=None,
                )

                result.frames[view] = (
                    frame.copy()
                )

            except Exception as exc:
                result.errors.append(
                    f"{view}: {exc}"
                )

        return result