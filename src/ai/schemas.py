from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnalyticsContext:
    """
    Safe analytical context supplied to the AI layer.

    Only aggregated / explicitly approved Nexus360 data
    should be placed inside this object.
    """

    page: str
    question: str

    metrics: dict[str, Any] = field(
        default_factory=dict
    )

    insights: list[str] = field(
        default_factory=list
    )

    definitions: dict[str, str] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class CopilotRequest:
    """
    Normalized request entering the Nexus360 AI layer.
    """

    question: str
    page: str = "general"


@dataclass(frozen=True)
class CopilotResponse:
    """
    Final response returned by Nexus360 Copilot.
    """

    answer: str
    model_name: str
    page: str

    grounded: bool = True