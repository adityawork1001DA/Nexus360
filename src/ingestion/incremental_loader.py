from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import bindparam, inspect, text
from sqlalchemy.engine import Engine

from src.database.audit import (
    finish_pipeline_run,
    start_pipeline_run,
)
from src.database.connection import get_engine
from src.ingestion.csv_loader import (
    _generate_record_hashes,
    _normalize_nulls,
    _validate_source_file,
    prepare_dataframe,
)


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass(frozen=True)
class IncrementalLoadConfig:
    filepath: str
    table_name: str
    source_system: str
    business_key: str


SYNTHETIC_INCREMENTAL_LOADS = (
    IncrementalLoadConfig(
        filepath="data/raw/synthetic_incremental/customers.csv",
        table_name="customers",
        source_system="synthetic_crm",
        business_key="customer_id",
    ),
    IncrementalLoadConfig(
        filepath="data/raw/synthetic_incremental/subscriptions.csv",
        table_name="subscriptions",
        source_system="synthetic_billing",
        business_key="subscription_id",
    ),
    IncrementalLoadConfig(
        filepath="data/raw/synthetic_incremental/revenue.csv",
        table_name="revenue",
        source_system="synthetic_billing",
        business_key="transaction_id",
    ),
    IncrementalLoadConfig(
        filepath="data/raw/synthetic_incremental/cloud_usage.csv",
        table_name="cloud_usage",
        source_system="synthetic_telemetry",
        business_key="usage_id",
    ),
    IncrementalLoadConfig(
        filepath="data/raw/synthetic_incremental/support_tickets.csv",
        table_name="support_tickets",
        source_system="synthetic_support",
        business_key="ticket_id",
    ),
)


# ============================================================
# RESULT MODEL
# ============================================================


@dataclass(frozen=True)
class IncrementalLoadResult:
    table_name: str
    rows_read: int
    rows_inserted: int
    rows_skipped: int
    before_count: int
    after_count: int


# ============================================================
# HELPERS
# ============================================================


def _validate_target_table(
    engine: Engine,
    table_name: str,
    business_key: str,
) -> None:
    """
    Ensure the approved RAW table and business key exist.
    """

    inspector = inspect(engine)

    if not inspector.has_table(
        table_name,
        schema="raw",
    ):
        raise ValueError(
            f"Target table raw.{table_name} does not exist."
        )

    columns = {
        column["name"]
        for column in inspector.get_columns(
            table_name,
            schema="raw",
        )
    }

    if business_key not in columns:
        raise ValueError(
            f"Business key '{business_key}' does not exist "
            f"in raw.{table_name}."
        )


def _table_count(
    engine: Engine,
    table_name: str,
) -> int:
    """
    Return current row count for an approved RAW table.
    """

    allowed_tables = {
        config.table_name
        for config in SYNTHETIC_INCREMENTAL_LOADS
    }

    if table_name not in allowed_tables:
        raise ValueError(
            f"Table is not approved for incremental loading: "
            f"{table_name}"
        )

    query = text(
        f'SELECT COUNT(*) FROM raw."{table_name}"'
    )

    with engine.connect() as connection:
        value = connection.execute(
            query
        ).scalar_one()

    return int(value)


def _existing_business_keys(
    engine: Engine,
    table_name: str,
    business_key: str,
    keys: list[str],
) -> set[str]:
    """
    Return keys already present in PostgreSQL.

    Query in chunks to avoid extremely large IN clauses.
    """

    if not keys:
        return set()

    existing: set[str] = set()

    chunk_size = 5000

    query = text(
        f"""
        SELECT "{business_key}"
        FROM raw."{table_name}"
        WHERE "{business_key}" IN :keys
        """
    ).bindparams(
        bindparam(
            "keys",
            expanding=True,
        )
    )

    with engine.connect() as connection:

        for start in range(
            0,
            len(keys),
            chunk_size,
        ):
            chunk = keys[
                start:start + chunk_size
            ]

            rows = connection.execute(
                query,
                {
                    "keys": chunk,
                },
            )

            existing.update(
                str(row[0])
                for row in rows
                if row[0] is not None
            )

    return existing


def _prepare_incremental_dataframe(
    *,
    dataframe: pd.DataFrame,
    table_name: str,
    source_system: str,
    source_file: str,
    run_id: int,
) -> pd.DataFrame:
    """
    Apply the same normalization and metadata contract used
    by the standard Nexus360 CSV ingestion engine.
    """

    business_columns = list(
        dataframe.columns
    )

    dataframe = prepare_dataframe(
        dataframe=dataframe,
        table_name=table_name,
    )

    dataframe["_record_hash"] = (
        _generate_record_hashes(
            dataframe=dataframe,
            business_columns=business_columns,
        )
    )

    dataframe["_source_system"] = (
        source_system
    )

    dataframe["_source_file"] = (
        source_file
    )

    dataframe["_run_id"] = run_id

    return _normalize_nulls(
        dataframe
    )


# ============================================================
# SINGLE DATASET LOAD
# ============================================================


def load_csv_incrementally(
    *,
    filepath: str,
    table_name: str,
    source_system: str,
    business_key: str,
    engine: Engine | None = None,
) -> IncrementalLoadResult:
    """
    Append only previously unseen business records.

    Existing RAW rows are never deleted or truncated.
    """

    db_engine = (
        engine
        or get_engine()
    )

    path = Path(filepath)

    _validate_source_file(
        path
    )

    _validate_target_table(
        db_engine,
        table_name,
        business_key,
    )

    run_id = start_pipeline_run(
        engine=db_engine,
        pipeline_name=(
            f"raw_{table_name}_incremental_load"
        ),
        source_name=source_system,
    )

    rows_read = 0
    rows_inserted = 0
    rows_skipped = 0

    before_count = _table_count(
        db_engine,
        table_name,
    )

    try:

        dataframe = pd.read_csv(
            path
        )

        rows_read = len(
            dataframe
        )

        if dataframe.empty:
            raise ValueError(
                f"Source CSV contains no records: {path}"
            )

        if business_key not in dataframe.columns:
            raise ValueError(
                f"Source file {path.name} does not contain "
                f"business key '{business_key}'."
            )

        if dataframe[
            business_key
        ].isna().any():
            raise ValueError(
                f"Source file {path.name} contains NULL "
                f"{business_key} values."
            )

        # ----------------------------------------------------
        # Remove duplicate IDs inside the incoming batch.
        # ----------------------------------------------------

        duplicate_mask = dataframe.duplicated(
            subset=[business_key],
            keep="first",
        )

        batch_duplicates = int(
            duplicate_mask.sum()
        )

        if batch_duplicates:
            dataframe = dataframe.loc[
                ~duplicate_mask
            ].copy()

        incoming_keys = (
            dataframe[business_key]
            .astype(str)
            .tolist()
        )

        existing_keys = (
            _existing_business_keys(
                db_engine,
                table_name,
                business_key,
                incoming_keys,
            )
        )

        existing_mask = (
            dataframe[business_key]
            .astype(str)
            .isin(existing_keys)
        )

        database_duplicates = int(
            existing_mask.sum()
        )

        dataframe = dataframe.loc[
            ~existing_mask
        ].copy()

        rows_skipped = (
            batch_duplicates
            + database_duplicates
        )

        # ----------------------------------------------------
        # Nothing new is still a successful idempotent run.
        # ----------------------------------------------------

        if dataframe.empty:

            after_count = before_count

            finish_pipeline_run(
                engine=db_engine,
                run_id=run_id,
                status="SUCCESS",
                rows_read=rows_read,
                rows_inserted=0,
                rows_updated=0,
                rows_rejected=rows_skipped,
                metadata={
                    "file": str(path),
                    "filename": path.name,
                    "table": f"raw.{table_name}",
                    "business_key": business_key,
                    "source_system": source_system,
                    "mode": "incremental",
                    "before_count": before_count,
                    "after_count": after_count,
                    "duplicates_skipped":
                        rows_skipped,
                },
            )

            return IncrementalLoadResult(
                table_name=table_name,
                rows_read=rows_read,
                rows_inserted=0,
                rows_skipped=rows_skipped,
                before_count=before_count,
                after_count=after_count,
            )

        dataframe = (
            _prepare_incremental_dataframe(
                dataframe=dataframe,
                table_name=table_name,
                source_system=source_system,
                source_file=path.name,
                run_id=run_id,
            )
        )

        # ----------------------------------------------------
        # APPEND ONLY.
        # No TRUNCATE.
        # No DELETE.
        # No destructive replacement.
        # ----------------------------------------------------

        dataframe.to_sql(
            name=table_name,
            con=db_engine,
            schema="raw",
            if_exists="append",
            index=False,
            chunksize=250,
        )

        rows_inserted = len(
            dataframe
        )

        after_count = _table_count(
            db_engine,
            table_name,
        )

        expected_after = (
            before_count
            + rows_inserted
        )

        if after_count != expected_after:
            raise RuntimeError(
                f"Row-count verification failed for "
                f"raw.{table_name}. Expected "
                f"{expected_after:,}, found "
                f"{after_count:,}."
            )

        finish_pipeline_run(
            engine=db_engine,
            run_id=run_id,
            status="SUCCESS",
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_updated=0,
            rows_rejected=rows_skipped,
            metadata={
                "file": str(path),
                "filename": path.name,
                "table": f"raw.{table_name}",
                "business_key": business_key,
                "source_system": source_system,
                "mode": "incremental",
                "before_count": before_count,
                "after_count": after_count,
                "duplicates_skipped":
                    rows_skipped,
            },
        )

        print(
            f"[OK] raw.{table_name:<20} "
            f"+{rows_inserted:>10,} new | "
            f"{rows_skipped:>10,} skipped | "
            f"{before_count:>10,} -> "
            f"{after_count:>10,}"
        )

        return IncrementalLoadResult(
            table_name=table_name,
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_skipped=rows_skipped,
            before_count=before_count,
            after_count=after_count,
        )

    except Exception as exc:

        finish_pipeline_run(
            engine=db_engine,
            run_id=run_id,
            status="FAILED",
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_updated=0,
            rows_rejected=rows_skipped,
            error_message=(
                f"{type(exc).__name__}: "
                f"{str(exc)[:2000]}"
            ),
            metadata={
                "file": str(path),
                "filename": path.name,
                "table": f"raw.{table_name}",
                "business_key": business_key,
                "source_system": source_system,
                "mode": "incremental",
                "before_count": before_count,
            },
        )

        raise


# ============================================================
# COMPLETE SYNTHETIC BATCH
# ============================================================


def load_synthetic_incrementally(
) -> list[IncrementalLoadResult]:
    """
    Incrementally load all Nexus360 synthetic datasets.
    """

    engine = get_engine()

    results: list[
        IncrementalLoadResult
    ] = []

    print()
    print("=" * 78)
    print(
        "NEXUS360 - INCREMENTAL SYNTHETIC INGESTION"
    )
    print("=" * 78)

    for config in SYNTHETIC_INCREMENTAL_LOADS:

        result = load_csv_incrementally(
            filepath=config.filepath,
            table_name=config.table_name,
            source_system=config.source_system,
            business_key=config.business_key,
            engine=engine,
        )

        results.append(
            result
        )

    total_inserted = sum(
        result.rows_inserted
        for result in results
    )

    total_skipped = sum(
        result.rows_skipped
        for result in results
    )

    print("-" * 78)
    print(
        f"Inserted: {total_inserted:,} | "
        f"Skipped: {total_skipped:,}"
    )
    print("=" * 78)

    return results