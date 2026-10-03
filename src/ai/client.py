from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from src.ai.config import AIConfig, get_ai_config


# ============================================================
# RESPONSE MODEL
# ============================================================


@dataclass(frozen=True)
class AIResponse:
    """
    Normalized response returned by the Nexus360 Gemini client.
    """

    text: str
    model_name: str

    @property
    def is_empty(self) -> bool:
        return not bool(self.text.strip())


# ============================================================
# GEMINI CLIENT
# ============================================================


class GeminiClient:
    """
    Controlled wrapper around the Google Gen AI SDK.

    Responsibilities
    ----------------
    - Gemini API communication
    - transient-failure retry handling
    - response normalization
    - safe application-level error messages

    Business context, semantic retrieval, grounding and
    guardrails belong to higher Nexus360 AI layers.
    """

    MAX_ATTEMPTS = 4

    INITIAL_BACKOFF_SECONDS = 1.0
    MAX_BACKOFF_SECONDS = 8.0
    JITTER_SECONDS = 0.25

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    RETRYABLE_ERROR_MARKERS = (
        "429",
        "500",
        "502",
        "503",
        "504",
        "resource_exhausted",
        "unavailable",
        "internal",
        "deadline_exceeded",
        "too many requests",
        "rate limit",
        "high demand",
        "temporarily unavailable",
        "service unavailable",
        "gateway timeout",
    )

    def __init__(
        self,
        config: AIConfig | None = None,
    ) -> None:

        self.config = config or get_ai_config()

        if not self.config.is_configured:
            raise RuntimeError(
                "Gemini is not configured. "
                "Set GEMINI_API_KEY in the environment."
            )

        self.client = genai.Client(
            api_key=self.config.api_key,
        )

    # ========================================================
    # GENERATION
    # ========================================================

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
    ) -> AIResponse:
        """
        Generate a text response from Gemini.

        Transient Gemini/API failures are retried with
        exponential backoff.

        Authentication, configuration and other non-transient
        failures fail immediately.
        """

        cleaned_prompt = str(prompt).strip()

        if not cleaned_prompt:
            raise ValueError(
                "Gemini prompt cannot be empty."
            )

        generation_config = self._build_generation_config(
            system_instruction=system_instruction,
        )

        last_exception: Exception | None = None

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1,
        ):

            try:
                response = (
                    self.client.models.generate_content(
                        model=self.config.model_name,
                        contents=cleaned_prompt,
                        config=generation_config,
                    )
                )

                text = self._extract_text(
                    response
                )

                return AIResponse(
                    text=text,
                    model_name=self.config.model_name,
                )

            except Exception as exc:

                last_exception = exc

                retryable = self._is_retryable_error(
                    exc
                )

                final_attempt = (
                    attempt >= self.MAX_ATTEMPTS
                )

                if (
                    not retryable
                    or final_attempt
                ):
                    break

                delay = self._retry_delay(
                    attempt=attempt,
                )

                time.sleep(delay)

        raise RuntimeError(
            self._safe_failure_message(
                exception=last_exception,
            )
        ) from last_exception

    # ========================================================
    # GENERATION CONFIG
    # ========================================================

    def _build_generation_config(
        self,
        *,
        system_instruction: str | None,
    ) -> types.GenerateContentConfig:
        """
        Build controlled Gemini generation configuration.
        """

        config = types.GenerateContentConfig()

        setattr(
            config,
            "max_output_tokens",
            self.config.max_output_tokens,
        )

        if system_instruction:

            cleaned_instruction = (
                str(system_instruction).strip()
            )

            if cleaned_instruction:
                setattr(
                    config,
                    "system_instruction",
                    cleaned_instruction,
                )

        return config

    # ========================================================
    # RETRY POLICY
    # ========================================================

    @classmethod
    def _is_retryable_error(
        cls,
        exception: Exception,
    ) -> bool:
        """
        Return True when an exception represents a temporary
        API/service failure.

        The implementation checks structured status attributes
        first and falls back to sanitized textual markers.
        """

        status_code = cls._extract_status_code(
            exception
        )

        if (
            status_code
            in cls.RETRYABLE_STATUS_CODES
        ):
            return True

        error_text = (
            f"{type(exception).__name__} "
            f"{exception}"
        ).lower()

        return any(
            marker in error_text
            for marker
            in cls.RETRYABLE_ERROR_MARKERS
        )

    @staticmethod
    def _extract_status_code(
        exception: Exception,
    ) -> int | None:
        """
        Best-effort extraction of an HTTP/API status code.
        """

        for attribute in (
            "status_code",
            "code",
        ):

            value = getattr(
                exception,
                attribute,
                None,
            )

            if isinstance(
                value,
                int,
            ):
                return value

            if isinstance(
                value,
                str,
            ):

                stripped = value.strip()

                if stripped.isdigit():
                    return int(stripped)

        response = getattr(
            exception,
            "response",
            None,
        )

        if response is not None:

            value = getattr(
                response,
                "status_code",
                None,
            )

            if isinstance(
                value,
                int,
            ):
                return value

        return None

    @classmethod
    def _retry_delay(
        cls,
        *,
        attempt: int,
    ) -> float:
        """
        Calculate exponential retry delay with small jitter.

        attempt=1 -> approximately 1 second
        attempt=2 -> approximately 2 seconds
        attempt=3 -> approximately 4 seconds
        """

        exponential_delay = (
            cls.INITIAL_BACKOFF_SECONDS
            * (2 ** (attempt - 1))
        )

        bounded_delay = min(
            exponential_delay,
            cls.MAX_BACKOFF_SECONDS,
        )

        jitter = random.uniform(
            0.0,
            cls.JITTER_SECONDS,
        )

        return bounded_delay + jitter

    # ========================================================
    # SAFE ERROR HANDLING
    # ========================================================

    def _safe_failure_message(
        self,
        *,
        exception: Exception | None,
    ) -> str:
        """
        Return an application-safe Gemini failure message.

        Raw exception text is intentionally excluded because
        provider errors can contain implementation details.
        """

        if exception is None:
            return (
                "Nexus360 AI Copilot could not complete "
                "the request."
            )

        if self._is_retryable_error(
            exception
        ):
            return (
                "Nexus360 AI Copilot is temporarily "
                "unavailable because the AI service is "
                "busy or rate-limited. Please try again "
                "shortly."
            )

        status_code = self._extract_status_code(
            exception
        )

        if status_code in {
            401,
            403,
        }:
            return (
                "Nexus360 AI Copilot could not authenticate "
                "with the configured AI service. "
                "Check the server-side Gemini configuration."
            )

        if status_code == 404:
            return (
                "Nexus360 AI Copilot could not access "
                "the configured Gemini model. "
                "Check the server-side model configuration."
            )

        return (
            "Nexus360 AI Copilot could not complete "
            "the request because the AI service returned "
            "an unexpected error."
        )

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    def health_check(
        self,
    ) -> AIResponse:
        """
        Perform a minimal Gemini connectivity test.

        No Nexus360 business or customer data is sent.
        """

        return self.generate(
            (
                "Reply with exactly this text and nothing else: "
                "NEXUS360_GEMINI_OK"
            ),
            system_instruction=(
                "Follow the user's formatting instruction "
                "exactly."
            ),
        )

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _extract_text(
        response: Any,
    ) -> str:
        """
        Safely normalize text returned by the Gemini SDK.
        """

        try:
            text = response.text

        except Exception as exc:
            raise RuntimeError(
                "Gemini returned a response but its text "
                "could not be extracted."
            ) from exc

        if text is None:
            raise RuntimeError(
                "Gemini returned no text response."
            )

        cleaned = str(
            text
        ).strip()

        if not cleaned:
            raise RuntimeError(
                "Gemini returned an empty text response."
            )

        return cleaned