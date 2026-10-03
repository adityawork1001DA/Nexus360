from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


logger = logging.getLogger(__name__)


class AnalyticsDataLoader:
    """
    Secure read-only data-access layer for the Nexus360
    analytics semantic layer.

    Only explicitly approved analytics views can be loaded
    through ``load_view``.

    Arbitrary SQL access is restricted to read-only
    SELECT / WITH statements.
    """

    # ============================================================
    # APPROVED ANALYTICS SEMANTIC VIEWS
    # ============================================================

    ALLOWED_VIEWS: set[str] = {
        # --------------------------------------------------------
        # Executive / Revenue
        # --------------------------------------------------------
        "v_monthly_revenue",
        "v_yoy_revenue_growth",
        "v_rolling_revenue",
        "v_product_revenue_rank",
        "v_regional_performance",
        "v_executive_kpis",

        # --------------------------------------------------------
        # Customer Analytics
        # --------------------------------------------------------
        "v_customer_360",
        "v_customer_pareto",
        "v_customer_rfm",
        "v_customer_value_tiers",
        "v_customer_cohort",

        # --------------------------------------------------------
        # Subscription / Retention
        # --------------------------------------------------------
        "v_subscription_health",
        "v_subscription_renewal_risk",

        # --------------------------------------------------------
        # Product / AI
        # --------------------------------------------------------
        "v_product_penetration",
        "v_ai_adoption",

        # --------------------------------------------------------
        # Support
        # --------------------------------------------------------
        "v_support_sla_performance",
        "v_support_resolution_percentiles",

        # --------------------------------------------------------
        # Cloud / FinOps / Operations
        # --------------------------------------------------------
        "v_cloud_finops",
        "v_customer_cloud_efficiency",
        "v_datacenter_operations",

        # --------------------------------------------------------
        # Sustainability / Weather
        # --------------------------------------------------------
        "v_cloud_sustainability",
        "v_weather_cloud_correlation",

        # --------------------------------------------------------
        # External / Economic Intelligence
        # --------------------------------------------------------
        "v_fx_exposure",
        "v_macroeconomic_revenue",
        "v_market_opportunity",

        # --------------------------------------------------------
        # Risk / Advanced Analytics
        # --------------------------------------------------------
        "v_revenue_anomalies",
        "v_revenue_at_risk",
        "v_business_health_score",
    }

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self) -> None:
        """
        Initialize the analytics loader using the project's
        configured SQLAlchemy engine.
        """

        self.engine = get_engine()

    # ============================================================
    # AVAILABLE VIEWS
    # ============================================================

    def available_views(self) -> list[str]:
        """
        Return all analytics views approved for access.

        Returns
        -------
        list[str]
            Alphabetically sorted approved semantic views.
        """

        return sorted(self.ALLOWED_VIEWS)

    # ============================================================
    # LOAD SEMANTIC VIEW
    # ============================================================

    def load_view(
        self,
        view_name: str,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Load an approved analytics semantic view.

        Parameters
        ----------
        view_name:
            Name of the view inside the PostgreSQL
            ``analytics`` schema.

        limit:
            Optional positive integer limiting the number
            of returned rows.

        Returns
        -------
        pandas.DataFrame
            Result of the analytics view.

        Raises
        ------
        ValueError
            If the requested view is not approved or the
            supplied limit is invalid.
        """

        # --------------------------------------------------------
        # Security: explicit semantic-layer allowlist
        # --------------------------------------------------------

        if view_name not in self.ALLOWED_VIEWS:
            raise ValueError(
                f"View '{view_name}' is not approved "
                "for analytics access."
            )

        # --------------------------------------------------------
        # Validate LIMIT
        # --------------------------------------------------------

        if limit is not None:
            if (
                not isinstance(limit, int)
                or isinstance(limit, bool)
                or limit <= 0
            ):
                raise ValueError(
                    "limit must be a positive integer or None."
                )

        # --------------------------------------------------------
        # Safe view query
        #
        # view_name is safe here because it must first exist
        # in the hard-coded ALLOWED_VIEWS set.
        # --------------------------------------------------------

        sql = (
            f'SELECT * '
            f'FROM analytics."{view_name}"'
        )

        if limit is not None:
            sql += " LIMIT :limit"

        logger.info(
            "Loading analytics view: analytics.%s",
            view_name,
        )

        # --------------------------------------------------------
        # Execute
        # --------------------------------------------------------

        with self.engine.connect() as connection:

            if limit is None:
                dataframe = pd.read_sql_query(
                    text(sql),
                    connection,
                )

            else:
                dataframe = pd.read_sql_query(
                    text(sql),
                    connection,
                    params={
                        "limit": limit,
                    },
                )

        logger.info(
            "Loaded analytics.%s: %s rows x %s columns",
            view_name,
            len(dataframe),
            len(dataframe.columns),
        )

        return dataframe

    # ============================================================
    # READ-ONLY QUERY EXECUTION
    # ============================================================

    def load_query(
        self,
        query: str,
        params: dict | None = None,
    ) -> pd.DataFrame:
        """
        Execute a controlled read-only SELECT/WITH query.

        This method is intended for internal analytics operations
        where loading a predefined semantic view is insufficient.

        Mutating SQL statements are rejected.
        """

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty."
            )

        cleaned = query.lower()

        # --------------------------------------------------------
        # Only SELECT / WITH statements are permitted
        # --------------------------------------------------------

        if not (
            cleaned.startswith("select")
            or cleaned.startswith("with")
        ):
            raise ValueError(
                "Only read-only SELECT/WITH queries are allowed."
            )

        # --------------------------------------------------------
        # Block obvious mutating SQL
        # --------------------------------------------------------

        forbidden_tokens = (
            " insert ",
            " update ",
            " delete ",
            " drop ",
            " alter ",
            " truncate ",
            " create ",
            " grant ",
            " revoke ",
            " merge ",
            " call ",
            " execute ",
            " copy ",
            " vacuum ",
            " reindex ",
            " cluster ",
            " refresh ",
        )

        # Normalize whitespace so newline-separated SQL is also
        # checked correctly.
        normalized = " ".join(
            cleaned.split()
        )

        padded = (
            f" {normalized} "
        )

        if any(
            token in padded
            for token in forbidden_tokens
        ):
            raise ValueError(
                "Potentially mutating SQL is not allowed."
            )

        logger.info(
            "Executing controlled read-only analytics query."
        )

        # --------------------------------------------------------
        # Execute
        # --------------------------------------------------------

        with self.engine.connect() as connection:

            dataframe = pd.read_sql_query(
                text(query),
                connection,
                params=params or {},
            )

        logger.info(
            "Read-only analytics query returned "
            "%s rows x %s columns.",
            len(dataframe),
            len(dataframe.columns),
        )

        return dataframe

    # ============================================================
    # LOAD MULTIPLE VIEWS
    # ============================================================

    def load_many(
        self,
        view_names: Iterable[str],
    ) -> dict[str, pd.DataFrame]:
        """
        Load multiple approved semantic views.

        Parameters
        ----------
        view_names:
            Iterable containing analytics view names.

        Returns
        -------
        dict[str, pandas.DataFrame]
            Dictionary keyed by semantic view name.
        """

        if isinstance(
            view_names,
            str,
        ):
            raise TypeError(
                "view_names must be an iterable of view names, "
                "not a single string."
            )

        names = list(
            view_names
        )

        if not names:
            return {}

        invalid_views = [
            name
            for name in names
            if name not in self.ALLOWED_VIEWS
        ]

        if invalid_views:
            raise ValueError(
                "The following views are not approved for "
                "analytics access: "
                + ", ".join(
                    sorted(
                        invalid_views
                    )
                )
            )

        logger.info(
            "Loading %s analytics views.",
            len(names),
        )

        datasets = {
            name: self.load_view(name)
            for name in names
        }

        logger.info(
            "Successfully loaded %s analytics views.",
            len(datasets),
        )

        return datasets