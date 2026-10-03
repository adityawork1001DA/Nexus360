from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================


load_dotenv()


# ============================================================
# AI CONFIGURATION
# ============================================================


@dataclass(frozen=True)
class AIConfig:
    """
    Runtime configuration for the Nexus360 AI Copilot.

    Secrets are loaded exclusively from environment variables.
    No API key should ever be committed to source control.
    """

    api_key: str
    model_name: str
    temperature: float
    max_output_tokens: int

    @property
    def is_configured(self) -> bool:
        """
        Return True when a Gemini API key is available.
        """

        return bool(self.api_key.strip())


def get_ai_config() -> AIConfig:
    """
    Build Nexus360 AI configuration from environment variables.

    Environment variables
    ---------------------
    GEMINI_API_KEY
        Google Gemini API key.

    GEMINI_MODEL
        Gemini model identifier.

    GEMINI_TEMPERATURE
        Generation temperature.

    GEMINI_MAX_OUTPUT_TOKENS
        Maximum generated response length.
    """

    return AIConfig(
        api_key=os.getenv(
            "GEMINI_API_KEY",
            "",
        ).strip(),
        model_name=os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        ).strip(),
        temperature=_get_float(
            "GEMINI_TEMPERATURE",
            default=0.2,
            minimum=0.0,
            maximum=2.0,
        ),
        max_output_tokens=_get_int(
            "GEMINI_MAX_OUTPUT_TOKENS",
            default=2048,
            minimum=128,
            maximum=8192,
        ),
    )


# ============================================================
# VALIDATION HELPERS
# ============================================================


def _get_float(
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Safely read and validate a float environment variable.
    """

    raw_value = os.getenv(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = float(raw_value)

    except ValueError as exc:
        raise ValueError(
            f"{name} must be a valid number."
        ) from exc

    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def _get_int(
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Safely read and validate an integer environment variable.
    """

    raw_value = os.getenv(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)

    except ValueError as exc:
        raise ValueError(
            f"{name} must be a valid integer."
        ) from exc

    if not minimum <= value <= maximum:
        raise ValueError(
            f"{name} must be between "
            f"{minimum} and {maximum}."
        )

    return value