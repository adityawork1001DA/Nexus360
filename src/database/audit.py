from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.engine import Engine


def start_pipeline_run(
    engine: Engine,
    pipeline_name: str,
    source_name: str,
) -> int:

    query = text(
        """
        INSERT INTO audit.pipeline_run (
            pipeline_name,
            source_name,
            status
        )
        VALUES (
            :pipeline_name,
            :source_name,
            'STARTED'
        )
        RETURNING run_id
        """
    )

    with engine.begin() as connection:

        run_id = connection.execute(
            query,
            {
                "pipeline_name":
                    pipeline_name,

                "source_name":
                    source_name,
            },
        ).scalar_one()

    return int(run_id)


def finish_pipeline_run(
    engine: Engine,
    run_id: int,
    status: str,
    rows_read: int = 0,
    rows_inserted: int = 0,
    rows_updated: int = 0,
    rows_rejected: int = 0,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> None:

    query = text(
        """
        UPDATE audit.pipeline_run

        SET
            status = :status,
            completed_at =
                CURRENT_TIMESTAMP,

            rows_read =
                :rows_read,

            rows_inserted =
                :rows_inserted,

            rows_updated =
                :rows_updated,

            rows_rejected =
                :rows_rejected,

            error_message =
                :error_message,

            metadata =
                CAST(
                    :metadata
                    AS JSONB
                )

        WHERE run_id = :run_id
        """
    )

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "status":
                    status,

                "rows_read":
                    rows_read,

                "rows_inserted":
                    rows_inserted,

                "rows_updated":
                    rows_updated,

                "rows_rejected":
                    rows_rejected,

                "error_message":
                    error_message,

                "metadata":
                    json.dumps(
                        metadata or {}
                    ),

                "run_id":
                    run_id,
            },
        )