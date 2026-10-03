from __future__ import annotations

import re


class AIGuardrails:
    """
    Application-level security controls for Nexus360 Copilot.
    """

    MAX_QUESTION_LENGTH = 2000

    BLOCKED_PATTERNS = (
        r"\bdrop\s+table\b",
        r"\btruncate\s+table\b",
        r"\bdelete\s+from\b",
        r"\balter\s+table\b",
        r"\binsert\s+into\b",
        r"\bupdate\s+\w+\s+set\b",
        r"\bgrant\s+",
        r"\brevoke\s+",
        r"\bcreate\s+table\b",
        r"\bcreate\s+user\b",
        r"\bexecute\s+immediate\b",
    )

    SECRET_PATTERNS = (
        r"\bapi[_\-\s]?key\b",
        r"\bpassword\b",
        r"\bsecret[_\-\s]?key\b",
        r"\baccess[_\-\s]?token\b",
        r"\brefresh[_\-\s]?token\b",
        r"\bprivate[_\-\s]?key\b",
        r"\bcredentials?\b",
        r"\benvironment\s+variables?\b",
        r"(?<!\w)\.env(?!\w)",
    )

    PROMPT_INJECTION_PATTERNS = (
        r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b",
        r"\bdisregard\s+(?:all\s+)?(?:previous|prior)\s+instructions\b",
        r"\boverride\s+(?:the\s+)?system\b",
        r"\breveal\s+(?:the\s+)?system\s+prompt\b",
        r"\bshow\s+(?:me\s+)?(?:the\s+)?system\s+prompt\b",
        r"\bprint\s+(?:the\s+)?system\s+prompt\b",
        r"\bdeveloper\s+message\b",
        r"\bhidden\s+instructions\b",
        r"\bjailbreak\b",
    )

    @classmethod
    def validate_question(
        cls,
        question: str,
    ) -> str:

        if not isinstance(
            question,
            str,
        ):
            raise ValueError(
                "Question must be a string."
            )

        cleaned = re.sub(
            r"\s+",
            " ",
            question.strip(),
        )

        if not cleaned:
            raise ValueError(
                "Question cannot be empty."
            )

        if len(cleaned) > cls.MAX_QUESTION_LENGTH:
            raise ValueError(
                "Question is too long."
            )

        for pattern in cls.BLOCKED_PATTERNS:

            if re.search(
                pattern,
                cleaned,
                flags=re.IGNORECASE,
            ):
                raise ValueError(
                    "Database modification instructions "
                    "are not permitted."
                )

        return cleaned

    @classmethod
    def contains_secret_request(
        cls,
        question: str,
    ) -> bool:

        return cls._matches_any(
            question,
            cls.SECRET_PATTERNS,
        )

    @classmethod
    def contains_prompt_injection(
        cls,
        question: str,
    ) -> bool:

        return cls._matches_any(
            question,
            cls.PROMPT_INJECTION_PATTERNS,
        )

    @classmethod
    def validate_safe_request(
        cls,
        question: str,
    ) -> str:

        cleaned = cls.validate_question(
            question
        )

        if cls.contains_secret_request(
            cleaned
        ):
            raise ValueError(
                "Requests for credentials, API keys, "
                "passwords, tokens or private configuration "
                "are not permitted."
            )

        if cls.contains_prompt_injection(
            cleaned
        ):
            raise ValueError(
                "Instructions attempting to override Nexus360 "
                "AI grounding or system controls are not "
                "permitted."
            )

        return cleaned

    @staticmethod
    def _matches_any(
        text: str,
        patterns: tuple[str, ...],
    ) -> bool:

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            is not None
            for pattern in patterns
        )