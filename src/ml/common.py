from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


def ensure_ml_directories() -> None:
    for path in (
        Path("models/artifacts"),
        Path("models/registry"),
        Path("reports/ml"),
        Path("reports/predictions"),
    ):
        path.mkdir(parents=True, exist_ok=True)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(k): json_safe(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        value = float(value)
        return value if np.isfinite(value) else None

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, float):
        return value if np.isfinite(value) else None

    return value


def write_json(
    data: dict[str, Any],
    path: str | Path,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        json.dump(
            json_safe(data),
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    return output


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()