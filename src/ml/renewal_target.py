from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.database.connection import get_engine


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RenewalTargetBundle:
    """
    Customer-level churn target dataset.

    Target:
        1 = customer has no active/in-force subscription
            at the observation cutoff.

        0 = customer has at least one active/in-force
            subscription at the observation cutoff.
    """

    targets: pd.DataFrame
    observation_cutoff: pd.Timestamp
    positive_label: int = 1
    negative_label: int = 0


class RenewalTargetBuilder:
    """
    Build a customer-level subscription churn target.

    Nexus 360 subscription data represents a snapshot containing:

        Active
        Expired

    Active subscriptions can legitimately have end dates after the
    observation cutoff. Therefore end_date <= cutoff must NOT be used
    as the only eligibility rule.

    Customer target definition
    --------------------------
    At observation cutoff:

        churn_target = 0
            if the customer has at least one subscription that:

                start_date <= cutoff
                AND
                subscription_status = 'Active'
                AND
                end_date > cutoff

        churn_target = 1
            if the customer has subscription history by the cutoff
            but has no active/in-force subscription at the cutoff.

    This produces a customer-state target appropriate for the synthetic
    warehouse snapshot.
    """

    VALID_STATUSES = {
        "Active",
        "Expired",
    }

    def __init__(
        self,
        observation_cutoff: str | pd.Timestamp | None = None,
    ) -> None:

        self.engine = get_engine()

        self.requested_cutoff = (
            pd.Timestamp(
                observation_cutoff
            ).normalize()
            if observation_cutoff is not None
            else None
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build(self) -> RenewalTargetBundle:

        subscriptions = (
            self._load_subscriptions()
        )

        self._validate_source(
            subscriptions
        )

        cutoff = self._resolve_cutoff(
            subscriptions
        )

        logger.info(
            "Customer churn observation cutoff: %s",
            cutoff.date(),
        )

        # ----------------------------------------------------
        # Only subscriptions that had started by the cutoff
        # belong to the observable customer history.
        # ----------------------------------------------------

        observed = subscriptions.loc[
            subscriptions[
                "start_date"
            ] <= cutoff
        ].copy()

        if observed.empty:
            raise ValueError(
                "No subscriptions existed on or before "
                f"observation cutoff {cutoff.date()}."
            )

        # ----------------------------------------------------
        # Status flags
        # ----------------------------------------------------

        observed["is_expired_status"] = (
            observed[
                "subscription_status"
            ]
            .eq("Expired")
            .astype(int)
        )

        observed["is_active_status"] = (
            observed[
                "subscription_status"
            ]
            .eq("Active")
            .astype(int)
        )

        # ----------------------------------------------------
        # In-force subscription at cutoff
        #
        # It must:
        #   - have started
        #   - be marked Active
        #   - have an end date after cutoff
        # ----------------------------------------------------

        observed["is_active_at_cutoff"] = (
            (
                observed[
                    "subscription_status"
                ].eq("Active")
            )
            & (
                observed[
                    "end_date"
                ] > cutoff
            )
        ).astype(int)

        # ----------------------------------------------------
        # Contract-value flags
        # ----------------------------------------------------

        observed[
            "active_contract_value_at_cutoff"
        ] = np.where(
            observed[
                "is_active_at_cutoff"
            ].eq(1),
            observed[
                "contract_value_usd"
            ],
            0.0,
        )

        observed[
            "expired_contract_value_usd"
        ] = np.where(
            observed[
                "is_expired_status"
            ].eq(1),
            observed[
                "contract_value_usd"
            ],
            0.0,
        )

        # ----------------------------------------------------
        # Customer aggregation
        # ----------------------------------------------------

        targets = (
            observed
            .groupby(
                [
                    "customer_id",
                    "customer_name",
                ],
                as_index=False,
            )
            .agg(
                observed_subscription_count=(
                    "subscription_id",
                    "nunique",
                ),
                active_subscription_count_at_cutoff=(
                    "is_active_at_cutoff",
                    "sum",
                ),
                expired_subscription_count=(
                    "is_expired_status",
                    "sum",
                ),
                active_status_subscription_count=(
                    "is_active_status",
                    "sum",
                ),
                total_contract_value_usd=(
                    "contract_value_usd",
                    "sum",
                ),
                active_contract_value_usd=(
                    "active_contract_value_at_cutoff",
                    "sum",
                ),
                expired_contract_value_usd=(
                    "expired_contract_value_usd",
                    "sum",
                ),
                earliest_subscription_start_date=(
                    "start_date",
                    "min",
                ),
                latest_subscription_start_date=(
                    "start_date",
                    "max",
                ),
                earliest_subscription_end_date=(
                    "end_date",
                    "min",
                ),
                latest_subscription_end_date=(
                    "end_date",
                    "max",
                ),
            )
        )

        # ----------------------------------------------------
        # TARGET
        #
        # No active contract at cutoff = churned.
        # ----------------------------------------------------

        targets["churn_target"] = (
            targets[
                "active_subscription_count_at_cutoff"
            ]
            .eq(0)
            .astype(int)
        )

        # ----------------------------------------------------
        # Descriptive target metadata
        # ----------------------------------------------------

        targets[
            "active_subscription_pct_at_cutoff"
        ] = np.where(
            targets[
                "observed_subscription_count"
            ] > 0,
            (
                targets[
                    "active_subscription_count_at_cutoff"
                ]
                / targets[
                    "observed_subscription_count"
                ]
                * 100.0
            ),
            0.0,
        )

        targets[
            "expired_subscription_pct"
        ] = np.where(
            targets[
                "observed_subscription_count"
            ] > 0,
            (
                targets[
                    "expired_subscription_count"
                ]
                / targets[
                    "observed_subscription_count"
                ]
                * 100.0
            ),
            0.0,
        )

        targets[
            "active_contract_value_pct"
        ] = np.where(
            targets[
                "total_contract_value_usd"
            ] > 0,
            (
                targets[
                    "active_contract_value_usd"
                ]
                / targets[
                    "total_contract_value_usd"
                ]
                * 100.0
            ),
            0.0,
        )

        targets[
            "expired_contract_value_pct"
        ] = np.where(
            targets[
                "total_contract_value_usd"
            ] > 0,
            (
                targets[
                    "expired_contract_value_usd"
                ]
                / targets[
                    "total_contract_value_usd"
                ]
                * 100.0
            ),
            0.0,
        )

        targets[
            "observation_cutoff"
        ] = cutoff

        targets[
            "customer_subscription_state"
        ] = np.where(
            targets[
                "churn_target"
            ].eq(1),
            "Churned",
            "Active",
        )

        # ----------------------------------------------------
        # Sort
        # ----------------------------------------------------

        targets = (
            targets
            .sort_values(
                [
                    "latest_subscription_start_date",
                    "customer_id",
                ]
            )
            .reset_index(
                drop=True
            )
        )

        self._validate_output(
            targets
        )

        churned = int(
            targets[
                "churn_target"
            ].sum()
        )

        retained = int(
            targets[
                "churn_target"
            ].eq(0)
            .sum()
        )

        logger.info(
            "Customer churn target built: "
            "%s customers, %s churned, %s active.",
            len(targets),
            churned,
            retained,
        )

        return RenewalTargetBundle(
            targets=targets,
            observation_cutoff=cutoff,
        )

    # ========================================================
    # SOURCE LOADING
    # ========================================================

    def _load_subscriptions(
        self,
    ) -> pd.DataFrame:

        query = """
            SELECT
                f.subscription_id,
                c.customer_id,
                c.customer_name,
                p.product_code,
                p.product_name,
                p.product_family,
                ds.full_date AS start_date,
                de.full_date AS end_date,
                f.billing_frequency,
                f.contract_value_usd,
                f.seats,
                f.subscription_status,
                f.auto_renew
            FROM warehouse.fact_subscription AS f
            INNER JOIN warehouse.dim_customer AS c
                ON c.customer_key = f.customer_key
            INNER JOIN warehouse.dim_product AS p
                ON p.product_key = f.product_key
            INNER JOIN warehouse.dim_date AS ds
                ON ds.date_key = f.start_date_key
            INNER JOIN warehouse.dim_date AS de
                ON de.date_key = f.end_date_key
        """

        with self.engine.connect() as connection:

            dataframe = (
                pd.read_sql_query(
                    text(query),
                    connection,
                )
            )

        dataframe[
            "start_date"
        ] = pd.to_datetime(
            dataframe[
                "start_date"
            ],
            errors="coerce",
        )

        dataframe[
            "end_date"
        ] = pd.to_datetime(
            dataframe[
                "end_date"
            ],
            errors="coerce",
        )

        dataframe[
            "contract_value_usd"
        ] = (
            pd.to_numeric(
                dataframe[
                    "contract_value_usd"
                ],
                errors="coerce",
            )
            .fillna(0.0)
        )

        dataframe[
            "seats"
        ] = (
            pd.to_numeric(
                dataframe[
                    "seats"
                ],
                errors="coerce",
            )
            .fillna(0)
        )

        return dataframe

    # ========================================================
    # OBSERVATION CUTOFF
    # ========================================================

    def _resolve_cutoff(
        self,
        subscriptions: pd.DataFrame,
    ) -> pd.Timestamp:

        if (
            self.requested_cutoff
            is not None
        ):
            return (
                self.requested_cutoff
            )

        latest_start = (
            subscriptions[
                "start_date"
            ]
            .dropna()
            .max()
        )

        if pd.isna(
            latest_start
        ):
            raise ValueError(
                "Cannot infer observation cutoff because "
                "subscription start dates are missing."
            )

        return pd.Timestamp(
            latest_start
        ).normalize()

    # ========================================================
    # SOURCE VALIDATION
    # ========================================================

    def _validate_source(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        required = {
            "subscription_id",
            "customer_id",
            "customer_name",
            "start_date",
            "end_date",
            "contract_value_usd",
            "subscription_status",
        }

        missing = sorted(
            required
            - set(
                dataframe.columns
            )
        )

        if missing:
            raise ValueError(
                "Subscription source is missing columns: "
                + ", ".join(
                    missing
                )
            )

        if dataframe.empty:
            raise ValueError(
                "Subscription source contains no rows."
            )

        if dataframe[
            "subscription_id"
        ].duplicated().any():
            raise ValueError(
                "Duplicate subscription_id values detected."
            )

        if dataframe[
            "customer_id"
        ].isna().any():
            raise ValueError(
                "Null customer_id values detected."
            )

        if dataframe[
            "start_date"
        ].isna().any():
            raise ValueError(
                "Null or invalid subscription "
                "start dates detected."
            )

        if dataframe[
            "end_date"
        ].isna().any():
            raise ValueError(
                "Null or invalid subscription "
                "end dates detected."
            )

        invalid_statuses = (
            set(
                dataframe[
                    "subscription_status"
                ]
                .dropna()
                .astype(str)
                .unique()
            )
            - self.VALID_STATUSES
        )

        if invalid_statuses:
            raise ValueError(
                "Unexpected subscription statuses: "
                + ", ".join(
                    sorted(
                        invalid_statuses
                    )
                )
            )

        if (
            dataframe[
                "end_date"
            ]
            < dataframe[
                "start_date"
            ]
        ).any():
            raise ValueError(
                "Subscription end date occurs before "
                "start date for one or more rows."
            )

    # ========================================================
    # TARGET VALIDATION
    # ========================================================

    @staticmethod
    def _validate_output(
        targets: pd.DataFrame,
    ) -> None:

        if targets.empty:
            raise ValueError(
                "Customer churn target contains no rows."
            )

        if targets[
            "customer_id"
        ].duplicated().any():
            raise ValueError(
                "Customer churn target must contain "
                "exactly one row per customer."
            )

        if targets[
            "customer_id"
        ].isna().any():
            raise ValueError(
                "Customer churn target contains "
                "null customer_id values."
            )

        labels = set(
            targets[
                "churn_target"
            ].unique()
        )

        if not labels.issubset(
            {0, 1}
        ):
            raise ValueError(
                "churn_target must contain "
                "only binary values 0 and 1."
            )

        if labels != {
            0,
            1,
        }:
            counts = (
                targets[
                    "churn_target"
                ]
                .value_counts()
                .to_dict()
            )

            raise ValueError(
                "Customer churn target requires both "
                "classes 0 and 1. "
                f"Observed distribution: {counts}"
            )

        if (
            targets[
                "observed_subscription_count"
            ] <= 0
        ).any():
            raise ValueError(
                "Every target customer must have at least "
                "one observed subscription."
            )

        percentage_columns = [
            "active_subscription_pct_at_cutoff",
            "expired_subscription_pct",
            "active_contract_value_pct",
            "expired_contract_value_pct",
        ]

        for column in percentage_columns:

            invalid = (
                (
                    targets[column]
                    < 0
                )
                | (
                    targets[column]
                    > 100
                )
            )

            if invalid.any():
                raise ValueError(
                    f"{column} contains values "
                    "outside the range 0-100."
                )

        # Logical consistency:
        # churned customers must have no active subscription.
        invalid_churn = (
            targets[
                "churn_target"
            ].eq(1)
            & targets[
                "active_subscription_count_at_cutoff"
            ].gt(0)
        )

        if invalid_churn.any():
            raise ValueError(
                "Invalid churn target detected: "
                "churned customer has an active "
                "subscription at cutoff."
            )

        # Active customers must have >= 1 active subscription.
        invalid_active = (
            targets[
                "churn_target"
            ].eq(0)
            & targets[
                "active_subscription_count_at_cutoff"
            ].eq(0)
        )

        if invalid_active.any():
            raise ValueError(
                "Invalid active target detected: "
                "non-churned customer has no active "
                "subscription at cutoff."
            )