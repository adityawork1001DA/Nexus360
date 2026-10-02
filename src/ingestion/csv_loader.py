from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.engine import Engine

from src.database.audit import (
    finish_pipeline_run,
    start_pipeline_run,
)
from src.database.connection import get_engine
from src.utils.hashing import create_record_hash


# ---------------------------------------------------------------------
# NEXUS 360
# Enterprise CSV -> PostgreSQL RAW ingestion engine
#
# Responsibilities:
#   1. Read source CSV files
#   2. Normalize source data types
#   3. Convert date columns to Python date objects
#   4. Convert nullable values to PostgreSQL-compatible None
#   5. Generate deterministic SHA-256 record hashes
#   6. Attach ingestion metadata
#   7. Load data into PostgreSQL RAW schema
#   8. Record pipeline execution in audit.pipeline_run
# ---------------------------------------------------------------------


DATE_COLUMNS_BY_TABLE: dict[str, list[str]] = {
    "customers": [
        "signup_date",
    ],

    "subscriptions": [
        "start_date",
        "end_date",
    ],

    "revenue": [
        "transaction_date",
    ],

    "cloud_usage": [
        "usage_date",
    ],

    "support_tickets": [
        "opened_date",
        "closed_date",
    ],
}


BOOLEAN_COLUMNS_BY_TABLE: dict[str, list[str]] = {
    "customers": [
        "is_ai_customer",
    ],

    "subscriptions": [
        "auto_renew",
    ],

    "support_tickets": [
        "sla_met",
        "reopened",
    ],
}


INTEGER_COLUMNS_BY_TABLE: dict[str, list[str]] = {
    "subscriptions": [
        "seats",
    ],

    "cloud_usage": [
        "requests_count",
        "failed_requests",
    ],
}


def _normalize_boolean_value(
    value: Any,
) -> bool | None:
    """
    Convert common CSV boolean representations into
    proper Python bool values.

    PostgreSQL BOOLEAN columns should receive bool/None,
    not arbitrary strings.
    """

    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    normalized = str(value).strip().lower()

    true_values = {
        "true",
        "t",
        "1",
        "yes",
        "y",
    }

    false_values = {
        "false",
        "f",
        "0",
        "no",
        "n",
    }

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    raise ValueError(
        f"Invalid boolean value: {value!r}"
    )


def _convert_date_columns(
    dataframe: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:
    """
    Convert CSV date strings into Python datetime.date objects.

    Example:
        '2024-12-07'
            ->
        datetime.date(2024, 12, 7)

    This is required because PostgreSQL DATE columns should
    not receive VARCHAR parameters through psycopg.
    """

    date_columns = DATE_COLUMNS_BY_TABLE.get(
        table_name,
        [],
    )

    for column in date_columns:

        if column not in dataframe.columns:
            continue

        converted = pd.to_datetime(
            dataframe[column],
            errors="coerce",
        )

        invalid_mask = (
            dataframe[column].notna()
            & converted.isna()
        )

        invalid_count = int(
            invalid_mask.sum()
        )

        if invalid_count > 0:

            examples = (
                dataframe.loc[
                    invalid_mask,
                    column,
                ]
                .astype(str)
                .head(5)
                .tolist()
            )

            raise ValueError(
                f"Table '{table_name}' contains "
                f"{invalid_count} invalid value(s) "
                f"in date column '{column}'. "
                f"Examples: {examples}"
            )

        dataframe[column] = (
            converted.dt.date
        )

    return dataframe


def _convert_boolean_columns(
    dataframe: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:
    """
    Normalize boolean columns before PostgreSQL insertion.
    """

    boolean_columns = (
        BOOLEAN_COLUMNS_BY_TABLE.get(
            table_name,
            [],
        )
    )

    for column in boolean_columns:

        if column not in dataframe.columns:
            continue

        dataframe[column] = (
            dataframe[column]
            .apply(
                _normalize_boolean_value
            )
        )

    return dataframe


def _convert_integer_columns(
    dataframe: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:
    """
    Validate and normalize integer columns.
    """

    integer_columns = (
        INTEGER_COLUMNS_BY_TABLE.get(
            table_name,
            [],
        )
    )

    for column in integer_columns:

        if column not in dataframe.columns:
            continue

        converted = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        invalid_mask = (
            dataframe[column].notna()
            & converted.isna()
        )

        invalid_count = int(
            invalid_mask.sum()
        )

        if invalid_count > 0:

            examples = (
                dataframe.loc[
                    invalid_mask,
                    column,
                ]
                .astype(str)
                .head(5)
                .tolist()
            )

            raise ValueError(
                f"Table '{table_name}' contains "
                f"{invalid_count} invalid integer "
                f"value(s) in column '{column}'. "
                f"Examples: {examples}"
            )

        dataframe[column] = (
            converted.astype("Int64")
        )

    return dataframe


def _normalize_nulls(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert Pandas missing values into Python None values
    before sending records to PostgreSQL.
    """

    return dataframe.astype(object).where(
        pd.notna(dataframe),
        None,
    )


def prepare_dataframe(
    dataframe: pd.DataFrame,
    table_name: str,
) -> pd.DataFrame:
    """
    Perform source-to-database type normalization.

    This function deliberately belongs in the ingestion
    layer so individual pipeline scripts do not duplicate
    datatype-conversion logic.
    """

    dataframe = dataframe.copy()

    dataframe = _convert_date_columns(
        dataframe=dataframe,
        table_name=table_name,
    )

    dataframe = _convert_boolean_columns(
        dataframe=dataframe,
        table_name=table_name,
    )

    dataframe = _convert_integer_columns(
        dataframe=dataframe,
        table_name=table_name,
    )

    dataframe = _normalize_nulls(
        dataframe
    )

    return dataframe


def _generate_record_hashes(
    dataframe: pd.DataFrame,
    business_columns: list[str],
) -> pd.Series:
    """
    Generate SHA-256 hashes from business/source columns.

    Ingestion metadata is deliberately excluded from the
    hash so rerunning the same source data produces the
    same business record hash.
    """

    return dataframe[
        business_columns
    ].apply(
        lambda row: create_record_hash(
            row.tolist()
        ),
        axis=1,
    )


def _validate_source_file(
    path: Path,
) -> None:
    """
    Perform basic source-file validation.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"CSV source file does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"CSV source path is not a file: {path}"
        )

    if path.suffix.lower() != ".csv":
        raise ValueError(
            f"Expected a CSV file but received: {path}"
        )


def _load_dataframe_to_postgres(
    dataframe: pd.DataFrame,
    engine: Engine,
    table_name: str,
) -> int:
    """
    Load the prepared DataFrame into PostgreSQL.

    We intentionally avoid method='multi'.

    Modern SQLAlchemy + psycopg can efficiently execute
    batches without generating an unnecessarily enormous
    multi-value INSERT statement.
    """

    if dataframe.empty:
        return 0

    dataframe.to_sql(
        name=table_name,
        con=engine,
        schema="raw",
        if_exists="append",
        index=False,
        chunksize=250,
    )

    return len(dataframe)


def load_csv_to_raw(
    filepath: str,
    table_name: str,
    source_system: str,
) -> None:
    """
    Load one CSV source into a PostgreSQL RAW table.

    The execution is tracked through audit.pipeline_run.
    """

    engine = get_engine()

    path = Path(filepath)

    _validate_source_file(
        path
    )

    run_id = start_pipeline_run(
        engine=engine,
        pipeline_name=(
            f"raw_{table_name}_load"
        ),
        source_name=source_system,
    )

    rows_read = 0
    rows_inserted = 0

    try:

        print(
            f"[START] {path.name} "
            f"-> raw.{table_name}"
        )

        # -------------------------------------------------------------
        # 1. Read source CSV
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # 2. Capture business/source columns BEFORE adding metadata
        # -------------------------------------------------------------

        business_columns = list(
            dataframe.columns
        )

        # -------------------------------------------------------------
        # 3. Normalize source datatypes
        # -------------------------------------------------------------

        dataframe = prepare_dataframe(
            dataframe=dataframe,
            table_name=table_name,
        )

        # -------------------------------------------------------------
        # 4. Generate record hashes
        # -------------------------------------------------------------

        dataframe[
            "_record_hash"
        ] = _generate_record_hashes(
            dataframe=dataframe,
            business_columns=business_columns,
        )

        # -------------------------------------------------------------
        # 5. Attach ingestion metadata
        # -------------------------------------------------------------

        dataframe[
            "_source_system"
        ] = source_system

        dataframe[
            "_source_file"
        ] = path.name

        dataframe[
            "_run_id"
        ] = run_id

        # -------------------------------------------------------------
        # 6. Final NULL normalization
        # -------------------------------------------------------------

        dataframe = _normalize_nulls(
            dataframe
        )

        # -------------------------------------------------------------
        # 7. PostgreSQL RAW load
        # -------------------------------------------------------------

        rows_inserted = (
            _load_dataframe_to_postgres(
                dataframe=dataframe,
                engine=engine,
                table_name=table_name,
            )
        )

        # -------------------------------------------------------------
        # 8. Audit successful execution
        # -------------------------------------------------------------

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="SUCCESS",
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_updated=0,
            rows_rejected=0,
            metadata={
                "file": str(path),
                "filename": path.name,
                "table": (
                    f"raw.{table_name}"
                ),
                "source_system":
                    source_system,
                "chunk_size":
                    250,
            },
        )

        print(
            f"[OK] {path.name:<25} "
            f"{rows_inserted:>12,} rows "
            f"-> raw.{table_name}"
        )

    except Exception as exc:

        # Keep the audit error readable.
        # SQLAlchemy exceptions may otherwise contain thousands
        # of bound parameters.

        full_error = str(exc)

        audit_error = (
            f"{type(exc).__name__}: "
            f"{full_error[:2000]}"
        )

        finish_pipeline_run(
            engine=engine,
            run_id=run_id,
            status="FAILED",
            rows_read=rows_read,
            rows_inserted=rows_inserted,
            rows_updated=0,
            rows_rejected=0,
            error_message=audit_error,
            metadata={
                "file": str(path),
                "filename": path.name,
                "table": (
                    f"raw.{table_name}"
                ),
                "source_system":
                    source_system,
            },
        )

        print()
        print(
            f"[FAILED] {path.name} "
            f"-> raw.{table_name}"
        )
        print(
            f"Reason: {type(exc).__name__}: "
            f"{full_error[:1000]}"
        )
        print()

        raise