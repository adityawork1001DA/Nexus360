from __future__ import annotations

import re
from dataclasses import dataclass

from src.ai.semantic_catalog import (
    SEMANTIC_DOMAINS,
)


@dataclass(frozen=True)
class IntentResult:
    """
    Deterministic analytical routing result.
    """

    primary_domain: str
    related_domains: tuple[str, ...]
    confidence: float
    matched_terms: tuple[str, ...]


class NexusIntentRouter:
    """
    Deterministic enterprise analytical intent router.

    Routing is intentionally performed without an LLM so that
    Nexus360 controls which semantic domain may be exposed to
    the grounding layer.

    Routing uses:

    1. Semantic-catalog keywords
    2. High-signal enterprise intent phrases
    3. Current dashboard page as a weak prior

    The user's actual question always has greater weight than
    the current page.
    """

    # ========================================================
    # HIGH-SIGNAL DOMAIN PHRASES
    # ========================================================

    DOMAIN_PHRASES: dict[str, tuple[str, ...]] = {
        "executive": (
            "executive",
            "business health",
            "company performance",
            "enterprise performance",
            "overall performance",
            "overall business",
            "business performance",
            "executive summary",
            "company summary",
            "management summary",
            "enterprise summary",
        ),
        "revenue": (
            "revenue",
            "sales",
            "regional revenue",
            "monthly revenue",
            "revenue growth",
            "revenue trend",
            "revenue performance",
            "revenue by region",
            "revenue by country",
            "revenue by product",
            "gross profit",
            "profitability",
            "commercial performance",
        ),
        "customer": (
            "customer",
            "customers",
            "customer retention",
            "retention",
            "subscription",
            "subscriptions",
            "renewal",
            "renewals",
            "customer value",
            "customer segment",
            "rfm",
            "cohort",
            "pareto",
            "customer health",
            "subscription health",
        ),
        "ml": (
            "churn",
            "churn risk",
            "churn probability",
            "churn prediction",
            "predictive",
            "prediction",
            "machine learning",
            "model",
            "model performance",
            "roc auc",
            "roc-auc",
            "pr auc",
            "pr-auc",
            "feature importance",
            "risk band",
            "critical risk",
            "predicted churn",
        ),
        "product": (
            "product",
            "products",
            "product performance",
            "product revenue",
            "product adoption",
            "product usage",
            "product portfolio",
            "ai product",
            "ai products",
            "service portfolio",
            "service adoption",
        ),
        "cloud": (
            "cloud",
            "cloud cost",
            "cloud costs",
            "cloud spend",
            "cloud spending",
            "cloud efficiency",
            "cloud infrastructure",
            "cloud operations",
            "cloud workload",
            "cloud workloads",
            "finops",
            "compute",
            "compute hours",
            "storage",
            "network gb",
            "network usage",
            "request failure",
            "failed requests",
            "data center",
            "data centers",
            "datacenter",
            "datacenters",
            "data centre",
            "data centres",
            "capacity mw",
            "renewable energy",
            "carbon",
            "carbon intensity",
            "carbon emissions",
            "sustainability",
            "sustainable",
            "weather",
            "temperature",
            "precipitation",
            "wind",
        ),
        "market": (
            "market",
            "markets",
            "market intelligence",
            "market performance",
            "economic",
            "economy",
            "gdp",
            "exchange rate",
            "exchange rates",
            "currency",
            "fx",
            "foreign exchange",
            "world bank",
            "macro",
            "macroeconomic",
        ),
    }

    # ========================================================
    # ROUTING
    # ========================================================

    def route(
        self,
        question: str,
        *,
        page: str = "general",
    ) -> IntentResult:
        """
        Route a question to the most relevant Nexus360 domain.
        """

        text = self._normalize(question)

        scores: dict[str, int] = {
            key: 0
            for key in SEMANTIC_DOMAINS
        }

        matches: dict[str, list[str]] = {
            key: []
            for key in SEMANTIC_DOMAINS
        }

        # ----------------------------------------------------
        # 1. Semantic catalog keyword matching
        # ----------------------------------------------------

        for key, domain in SEMANTIC_DOMAINS.items():

            for keyword in domain.keywords:

                normalized_keyword = self._normalize(
                    keyword
                )

                if not normalized_keyword:
                    continue

                if self._contains_term(
                    text,
                    normalized_keyword,
                ):
                    scores[key] += self._catalog_weight(
                        normalized_keyword
                    )

                    self._append_match(
                        matches[key],
                        keyword,
                    )

        # ----------------------------------------------------
        # 2. High-signal enterprise phrase matching
        # ----------------------------------------------------

        for domain_key, phrases in (
            self.DOMAIN_PHRASES.items()
        ):

            if domain_key not in scores:
                continue

            for phrase in phrases:

                normalized_phrase = self._normalize(
                    phrase
                )

                if self._contains_term(
                    text,
                    normalized_phrase,
                ):
                    scores[domain_key] += (
                        self._phrase_weight(
                            normalized_phrase
                        )
                    )

                    self._append_match(
                        matches[domain_key],
                        phrase,
                    )

        # ----------------------------------------------------
        # 3. Contextual compound-intent bonuses
        # ----------------------------------------------------

        self._apply_compound_rules(
            text=text,
            scores=scores,
            matches=matches,
        )

        # ----------------------------------------------------
        # 4. Current page = weak prior only
        # ----------------------------------------------------

        normalized_page = self._normalize_page(
            page
        )

        if normalized_page in scores:
            scores[normalized_page] += 1

        # ----------------------------------------------------
        # 5. Rank domains
        # ----------------------------------------------------

        ranked = sorted(
            scores,
            key=lambda key: (
                scores[key],
                key == normalized_page,
            ),
            reverse=True,
        )

        best = ranked[0]

        # No meaningful question match:
        # use current valid page, otherwise executive.
        if scores[best] <= 0:

            best = (
                normalized_page
                if normalized_page in SEMANTIC_DOMAINS
                else self._default_domain()
            )

        related = tuple(
            key
            for key in ranked
            if (
                key != best
                and scores[key] > 0
            )
        )[:2]

        confidence = self._confidence(
            best_score=max(
                scores.get(best, 0),
                0,
            ),
            second_score=self._second_score(
                ranked=ranked,
                scores=scores,
                best=best,
            ),
        )

        return IntentResult(
            primary_domain=best,
            related_domains=related,
            confidence=confidence,
            matched_terms=tuple(
                matches.get(
                    best,
                    [],
                )
            ),
        )

    # ========================================================
    # COMPOUND DOMAIN RULES
    # ========================================================

    def _apply_compound_rules(
        self,
        *,
        text: str,
        scores: dict[str, int],
        matches: dict[str, list[str]],
    ) -> None:
        """
        Apply deterministic bonuses for highly specific
        analytical intents.

        These rules help resolve ambiguous words such as cost,
        capacity, sustainability and weather.
        """

        if "cloud" in scores:

            cloud_patterns = (
                (
                    r"\bcloud\b.*\b(cost|spend|spending)\b",
                    "cloud cost",
                ),
                (
                    r"\b(cost|spend|spending)\b.*\bcloud\b",
                    "cloud cost",
                ),
                (
                    r"\bcloud\b.*\b(efficien\w*|optim\w*)\b",
                    "cloud efficiency",
                ),
                (
                    r"\b(data\s*cent(?:er|re)s?|datacenters?)\b",
                    "datacenter",
                ),
                (
                    r"\b(capacity|workload)\b.*\b(data\s*cent(?:er|re)s?|datacenters?)\b",
                    "datacenter capacity",
                ),
                (
                    r"\b(renewable|carbon|sustainab\w*)\b",
                    "cloud sustainability",
                ),
                (
                    r"\b(weather|temperature|precipitation|wind)\b",
                    "weather cloud operations",
                ),
                (
                    r"\b(compute|storage|network)\b.*\b(cost|usage|workload|capacity)\b",
                    "cloud infrastructure",
                ),
            )

            for pattern, label in cloud_patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    scores["cloud"] += 6

                    self._append_match(
                        matches["cloud"],
                        label,
                    )

        if "ml" in scores:

            ml_patterns = (
                (
                    r"\b(churn|attrition)\b.*\b(risk|probabilit\w*|predict\w*)\b",
                    "churn risk",
                ),
                (
                    r"\b(model|machine learning)\b.*\b(performance|metric|accuracy|auc)\b",
                    "model performance",
                ),
                (
                    r"\b(feature importance|risk band|predicted churn)\b",
                    "predictive churn",
                ),
            )

            for pattern, label in ml_patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    scores["ml"] += 6

                    self._append_match(
                        matches["ml"],
                        label,
                    )
        if "market" in scores:

            market_patterns = (
                (
                    r"\b(exchange rates?|foreign exchange|fx)\b",
                    "fx intelligence",
                ),
                (
                    r"\b(currency|currencies)\b.*\b(exposure|risk|volatil\w*|rate)\b",
                    "currency risk",
                ),
                (
                    r"\b(exposure|risk|volatil\w*|rate)\b.*\b(currency|currencies)\b",
                    "currency risk",
                ),
                (
                    r"\b(gdp|inflation|macroeconomic|econom\w*)\b",
                    "macroeconomic intelligence",
                ),
                (
                    r"\b(markets?|countr(?:y|ies))\b.*\b(opportunit\w*|whitespace|priorit\w*)\b",
                    "market opportunity",
                ),
                (
                    r"\b(digital readiness|internet usage|internet users)\b",
                    "digital readiness",
                ),
            )

            for pattern, label in market_patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    scores["market"] += 6

                    self._append_match(
                        matches["market"],
                        label,
                    )

        if "product" in scores:

            product_patterns = (
                (
                    r"\b(products?|sku)\b.*\b(revenue|sales|performance|adoption|usage)\b",
                    "product performance",
                ),
                (
                    r"\b(revenue|sales|performance|adoption|usage)\b.*\b(products?|sku)\b",
                    "product performance",
                ),
                (
                    r"\b(ai product|ai products|ai adoption)\b",
                    "ai product intelligence",
                ),
            )

            for pattern, label in product_patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    scores["product"] += 7

                    self._append_match(
                        matches["product"],
                        label,
                    )

        if "revenue" in scores:

            revenue_patterns = (
                (
                    r"\brevenue\b.*\b(region|country|month|product)\b",
                    "revenue analysis",
                ),
                (
                    r"\b(region|country|month|product)\b.*\brevenue\b",
                    "revenue analysis",
                ),
                (
                    r"\b(gross profit|profitability)\b",
                    "profitability",
                ),
            )

            for pattern, label in revenue_patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    scores["revenue"] += 5

                    self._append_match(
                        matches["revenue"],
                        label,
                    )

        if "customer" in scores:

            customer_patterns = (
                (
                    r"\bcustomer\b.*\b(retention|renewal|subscription|value|segment)\b",
                    "customer intelligence",
                ),
                (
                    r"\b(retention|renewal|subscription)\b.*\bcustomer\b",
                    "customer intelligence",
                ),
                (
                    r"\b(rfm|cohort|pareto)\b",
                    "customer analytics",
                ),
            )

            for pattern, label in customer_patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    scores["customer"] += 5

                    self._append_match(
                        matches["customer"],
                        label,
                    )

    # ========================================================
    # TEXT HELPERS
    # ========================================================

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        """
        Normalize text for deterministic matching.
        """

        text = str(
            value or ""
        ).lower()

        text = text.replace(
            "_",
            " ",
        )

        text = re.sub(
            r"[-/]+",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    @classmethod
    def _normalize_page(
        cls,
        page: str,
    ) -> str:

        normalized = cls._normalize(
            page
        )

        aliases = {
            "predictive ml": "ml",
            "machine learning": "ml",
            "ai copilot": "general",
            "executive command center": "executive",
            "revenue intelligence": "revenue",
            "customer intelligence": "customer",
            "product intelligence": "product",
            "cloud finops": "cloud",
            "cloud intelligence": "cloud",
            "market intelligence": "market",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    @staticmethod
    def _contains_term(
        text: str,
        term: str,
    ) -> bool:
        """
        Match complete terms while supporting multi-word
        enterprise phrases.
        """

        if not term:
            return False

        pattern = (
            r"(?<!\w)"
            + re.escape(term).replace(
                r"\ ",
                r"\s+",
            )
            + r"(?!\w)"
        )

        return (
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            is not None
        )

    # ========================================================
    # SCORING HELPERS
    # ========================================================

    @staticmethod
    def _catalog_weight(
        keyword: str,
    ) -> int:

        words = keyword.split()

        if len(words) >= 3:
            return 5

        if len(words) == 2:
            return 4

        return 2

    @staticmethod
    def _phrase_weight(
        phrase: str,
    ) -> int:

        words = phrase.split()

        if len(words) >= 3:
            return 8

        if len(words) == 2:
            return 6

        return 3

    @staticmethod
    def _append_match(
        matches: list[str],
        value: str,
    ) -> None:

        if value not in matches:
            matches.append(value)

    @staticmethod
    def _second_score(
        *,
        ranked: list[str],
        scores: dict[str, int],
        best: str,
    ) -> int:

        for key in ranked:

            if key != best:
                return max(
                    scores.get(key, 0),
                    0,
                )

        return 0

    @staticmethod
    def _confidence(
        *,
        best_score: int,
        second_score: int,
    ) -> float:
        """
        Produce a deterministic routing-confidence indicator.

        This is routing confidence, not ML probability.
        """

        if best_score <= 0:
            return 0.45

        margin = max(
            best_score - second_score,
            0,
        )

        confidence = (
            0.50
            + min(best_score, 20) * 0.018
            + min(margin, 12) * 0.012
        )

        return round(
            min(
                confidence,
                0.98,
            ),
            2,
        )

    @staticmethod
    def _default_domain() -> str:
        """
        Return a safe fallback domain that exists in the
        semantic catalog.
        """

        if "executive" in SEMANTIC_DOMAINS:
            return "executive"

        return next(
            iter(SEMANTIC_DOMAINS)
        )