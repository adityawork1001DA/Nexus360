from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


@dataclass
class PipelineStep:
    name: str
    script: str
    args: tuple[str, ...] = ()
    timeout: int = 1200


@dataclass
class PipelineResult:
    success: bool
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str | None = None
    logs: list[str] = field(default_factory=list)


PIPELINE = (
    PipelineStep(
        "Generate incremental enterprise data",
        "generate_incremental_enterprise_data.py",
        timeout=1200,
    ),
    PipelineStep(
        "Append incremental data to PostgreSQL",
        "load_synthetic_incremental.py",
        timeout=1200,
    ),
    PipelineStep(
        "Refresh analytics semantic layer",
        "build_analytics.py",
        timeout=1200,
    ),
    PipelineStep(
        "Refresh current churn predictions",
        "predict_current_churn.py",
        timeout=1200,
    ),
    PipelineStep(
        "Generate Excel executive report",
        "build_excel_report.py",
        timeout=1200,
    ),
)


def run_script(
    script_name: str,
    *args: str,
    timeout: int = 1200,
) -> tuple[bool, str]:

    script = SCRIPTS_DIR / script_name

    if not script.exists():
        return False, f"Missing script: {script}"

    env = os.environ.copy()

    current_pythonpath = env.get("PYTHONPATH", "")
    root = str(PROJECT_ROOT)

    env["PYTHONPATH"] = (
        root + os.pathsep + current_pythonpath
        if current_pythonpath
        else root
    )

    command = [
        sys.executable,
        str(script),
        *args,
    ]

    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    except subprocess.TimeoutExpired:
        return (
            False,
            f"{script_name} exceeded {timeout} seconds.",
        )

    except Exception as exc:
        return (
            False,
            f"{script_name} failed to start: {exc}",
        )

    output = "\n\n".join(
        value.strip()
        for value in (
            result.stdout,
            result.stderr,
        )
        if value and value.strip()
    )

    if result.returncode != 0:
        return (
            False,
            output
            or f"{script_name} exited with code "
               f"{result.returncode}.",
        )

    return (
        True,
        output or f"{script_name} completed.",
    )


def run_platform_refresh(
    *,
    customers: int = 25,
) -> PipelineResult:

    if customers < 1 or customers > 1000:
        raise ValueError(
            "customers must be between 1 and 1000."
        )

    completed: list[str] = []
    logs: list[str] = []

    for step in PIPELINE:

        args = step.args

        if (
            step.script
            == "generate_incremental_enterprise_data.py"
        ):
            args = (
                "--customers",
                str(customers),
            )

        ok, output = run_script(
            step.script,
            *args,
            timeout=step.timeout,
        )

        logs.append(
            f"\n{'=' * 70}\n"
            f"{step.name}\n"
            f"{'=' * 70}\n"
            f"{output}"
        )

        if not ok:
            return PipelineResult(
                success=False,
                completed_steps=completed,
                failed_step=step.name,
                logs=logs,
            )

        completed.append(step.name)

    return PipelineResult(
        success=True,
        completed_steps=completed,
        logs=logs,
    )