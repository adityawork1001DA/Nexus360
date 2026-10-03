from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from sqlalchemy import text

from src.database.connection import get_engine
from src.ui.data_service import (
    clear_dashboard_cache,
    load_analytics_view,
)
from src.ui.theme import render_page_header


# ============================================================
# NEXUS360 ADMIN CONTROL CENTER
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
POWERBI_DIR = ARTIFACTS_DIR / "powerbi"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

PIPELINE_SCRIPT = SCRIPTS_DIR / "run_pipeline.py"
EXTERNAL_INGEST_SCRIPT = (
    SCRIPTS_DIR / "ingest_external_data.py"
)
EXCEL_REPORT_SCRIPT = (
    SCRIPTS_DIR / "build_excel_report.py"
)

PIPELINE_TIMEOUT = 3600
UTILITY_TIMEOUT = 1800

ADMIN_MONITOR_VIEWS = (
    "v_executive_kpis",
    "v_monthly_revenue",
    "v_customer_360",
    "v_product_revenue_rank",
    "v_cloud_finops",
    "v_market_opportunity",
    "v_ai_adoption",
    "v_subscription_health",
    "v_support_sla_performance",
)

NAVIGATION_TARGETS = (
    ("Executive", "executive"),
    ("Revenue", "revenue"),
    ("Customer", "customer"),
    ("Product & AI", "product"),
    ("Cloud & FinOps", "cloud"),
    ("Support", "support"),
    ("Predictive ML", "ml"),
    ("AI Copilot", "ai"),
)


# ============================================================
# SCRIPT EXECUTION
# ============================================================

def _python_environment() -> dict[str, str]:
    env = os.environ.copy()

    root = str(PROJECT_ROOT)
    existing = env.get(
        "PYTHONPATH",
        "",
    )

    env["PYTHONPATH"] = (
        root
        + (
            os.pathsep + existing
            if existing
            else ""
        )
    )

    return env


def _run_python_script(
    script_path: Path,
    *args: str,
    timeout: int = UTILITY_TIMEOUT,
) -> tuple[bool, str]:
    """
    Run one explicitly approved Nexus360 Python script.

    Arbitrary shell commands are intentionally not exposed
    through the Admin UI.
    """

    if not script_path.exists():
        return (
            False,
            f"Script not found: {script_path}",
        )

    command = [
        sys.executable,
        str(script_path),
        *args,
    ]

    try:
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=_python_environment(),
        )

    except subprocess.TimeoutExpired as exc:
        partial_stdout = (
            exc.stdout.decode()
            if isinstance(exc.stdout, bytes)
            else exc.stdout
        )

        partial_stderr = (
            exc.stderr.decode()
            if isinstance(exc.stderr, bytes)
            else exc.stderr
        )

        output = "\n".join(
            part
            for part in (
                partial_stdout,
                partial_stderr,
            )
            if part
        )

        return (
            False,
            (
                f"Operation exceeded the "
                f"{timeout}-second timeout.\n\n"
                f"{output}"
            ).strip(),
        )

    except Exception as exc:
        return (
            False,
            (
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        )

    output = "\n\n".join(
        part.strip()
        for part in (
            result.stdout,
            result.stderr,
        )
        if part and part.strip()
    )

    if result.returncode != 0:
        return (
            False,
            output
            or (
                "Script failed with exit code "
                f"{result.returncode}."
            ),
        )

    return (
        True,
        output
        or "Operation completed successfully.",
    )


def _run_platform_pipeline(
    customers: int,
) -> tuple[bool, str]:
    """
    Run the canonical Nexus360 pipeline.

    scripts/run_pipeline.py is the single source of truth
    for generation, RAW ingestion, transformations,
    analytics, ML and Excel reporting.
    """

    if customers < 1 or customers > 1000:
        return (
            False,
            (
                "Customer count must be "
                "between 1 and 1000."
            ),
        )

    success, output = _run_python_script(
        PIPELINE_SCRIPT,
        "--customers",
        str(customers),
        timeout=PIPELINE_TIMEOUT,
    )

    if success:
        clear_dashboard_cache()

    return success, output


def _run_refresh_only() -> tuple[bool, str]:
    """
    Propagate existing RAW data without generating
    additional customers.
    """

    success, output = _run_python_script(
        PIPELINE_SCRIPT,
        "--refresh-only",
        timeout=PIPELINE_TIMEOUT,
    )

    if success:
        clear_dashboard_cache()

    return success, output


# ============================================================
# DATABASE HEALTH / COUNTS
# ============================================================

def _scalar_count(
    query: str,
) -> int:
    engine = get_engine()

    with engine.connect() as connection:
        value = connection.execute(
            text(query)
        ).scalar_one()

    return int(value or 0)


def _database_health() -> tuple[bool, str]:
    try:
        engine = get_engine()

        with engine.connect() as connection:
            value = connection.execute(
                text("SELECT 1")
            ).scalar_one()

        if int(value) != 1:
            return (
                False,
                "Unexpected PostgreSQL health response.",
            )

        return (
            True,
            "PostgreSQL connection responding normally.",
        )

    except Exception as exc:
        return (
            False,
            f"{type(exc).__name__}: {exc}",
        )


def _customer_propagation() -> dict[str, Any]:
    queries = {
        "RAW": (
            "SELECT COUNT(*) "
            "FROM raw.customers"
        ),
        "STAGING": (
            "SELECT COUNT(*) "
            "FROM staging.customers"
        ),
        "WAREHOUSE": (
            "SELECT COUNT(*) "
            "FROM warehouse.dim_customer"
        ),
        "ANALYTICS": (
            "SELECT COUNT(*) "
            "FROM analytics.v_customer_360"
        ),
    }

    counts: dict[str, int | None] = {}
    errors: list[str] = []

    engine = get_engine()

    with engine.connect() as connection:
        for label, query in queries.items():
            try:
                value = connection.execute(
                    text(query)
                ).scalar_one()

                counts[label] = int(
                    value or 0
                )

            except Exception as exc:
                counts[label] = None

                errors.append(
                    f"{label}: "
                    f"{type(exc).__name__}: {exc}"
                )

    available = [
        value
        for value in counts.values()
        if value is not None
    ]

    synchronized = (
        len(available) == len(queries)
        and len(set(available)) == 1
    )

    return {
        "counts": counts,
        "synchronized": synchronized,
        "errors": errors,
    }


def _platform_counts() -> list[dict[str, Any]]:
    definitions = (
        (
            "Customers",
            "raw.customers",
            (
                "SELECT COUNT(*) "
                "FROM raw.customers"
            ),
        ),
        (
            "Subscriptions",
            "raw.subscriptions",
            (
                "SELECT COUNT(*) "
                "FROM raw.subscriptions"
            ),
        ),
        (
            "Revenue Transactions",
            "raw.revenue",
            (
                "SELECT COUNT(*) "
                "FROM raw.revenue"
            ),
        ),
        (
            "Cloud Usage",
            "raw.cloud_usage",
            (
                "SELECT COUNT(*) "
                "FROM raw.cloud_usage"
            ),
        ),
        (
            "Support Tickets",
            "raw.support_tickets",
            (
                "SELECT COUNT(*) "
                "FROM raw.support_tickets"
            ),
        ),
    )

    rows: list[dict[str, Any]] = []

    for label, source, query in definitions:
        try:
            count = _scalar_count(
                query
            )

            rows.append(
                {
                    "Dataset": label,
                    "Source": source,
                    "Rows": count,
                    "Status": "Online",
                }
            )

        except Exception as exc:
            rows.append(
                {
                    "Dataset": label,
                    "Source": source,
                    "Rows": None,
                    "Status": (
                        f"Error: {exc}"
                    ),
                }
            )

    return rows


def _view_status(
    view_name: str,
) -> dict[str, Any]:
    try:
        frame = load_analytics_view(
            view_name,
            limit=5,
        )

        return {
            "View": view_name,
            "Status": "Online",
            "Sample Rows": len(frame),
            "Columns": len(frame.columns),
            "Error": "",
        }

    except Exception as exc:
        return {
            "View": view_name,
            "Status": "Error",
            "Sample Rows": 0,
            "Columns": 0,
            "Error": str(exc),
        }


# ============================================================
# ARTIFACT HELPERS
# ============================================================

def _format_timestamp(
    timestamp: float,
) -> str:
    return datetime.fromtimestamp(
        timestamp
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def _find_powerbi_file() -> Path | None:
    candidates: list[Path] = []

    directories = (
        POWERBI_DIR,
        ARTIFACTS_DIR,
        PROJECT_ROOT,
    )

    for directory in directories:
        if not directory.exists():
            continue

        candidates.extend(
            directory.glob("*.pbix")
        )

        candidates.extend(
            directory.glob("*.pbit")
        )

    if not candidates:
        for pattern in (
            "**/*.pbix",
            "**/*.pbit",
        ):
            candidates.extend(
                PROJECT_ROOT.glob(pattern)
            )

    candidates = [
        path
        for path in candidates
        if path.is_file()
        and "venv" not in path.parts
        and ".git" not in path.parts
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime
        ),
    )


def _find_excel_report() -> Path | None:
    candidates: list[Path] = []

    directories = (
        REPORTS_DIR,
        ARTIFACTS_DIR,
        PROJECT_ROOT / "reports" / "excel",
        PROJECT_ROOT,
    )

    for directory in directories:
        if directory.exists():
            candidates.extend(
                directory.glob("*.xlsx")
            )

    candidates = [
        path
        for path in candidates
        if path.is_file()
        and "venv" not in path.parts
        and ".git" not in path.parts
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime
        ),
    )


def _read_binary(
    path: Path,
) -> bytes:
    return path.read_bytes()


def _open_local_file(
    path: Path,
) -> tuple[bool, str]:
    """
    Open a local artifact using the host operating system.

    This is useful for a locally hosted Streamlit application.
    It does not refresh the Power BI semantic model.
    """

    if not path.exists():
        return (
            False,
            f"File not found: {path}",
        )

    try:
        if os.name == "nt":
            os.startfile(
                str(path)
            )

        elif sys.platform == "darwin":
            subprocess.Popen(
                ["open", str(path)]
            )

        else:
            subprocess.Popen(
                ["xdg-open", str(path)]
            )

        return (
            True,
            f"Opened {path.name}",
        )

    except Exception as exc:
        return (
            False,
            (
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        )


# ============================================================
# UI HELPERS
# ============================================================

def _render_admin_css() -> None:
    st.markdown(
        """
        <style>
        .admin-card {
            border: 1px solid #233650;
            border-radius: 16px;
            padding: 1rem 1.1rem;
            background:
                linear-gradient(
                    180deg,
                    rgba(19,34,56,.96),
                    rgba(15,27,45,.96)
                );
            min-height: 125px;
        }

        .admin-label {
            color: #94A3B8;
            font-size: .76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .06em;
        }

        .admin-value {
            color: #F8FAFC;
            font-size: 1.30rem;
            font-weight: 750;
            margin-top: .45rem;
        }

        .admin-detail {
            color: #94A3B8;
            font-size: .78rem;
            margin-top: .45rem;
            line-height: 1.45;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _status_card(
    label: str,
    value: str,
    detail: str,
) -> None:
    st.markdown(
        f"""
        <div class="admin-card">
          <div class="admin-label">{label}</div>
          <div class="admin-value">{value}</div>
          <div class="admin-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_operation_result(
    success: bool,
    output: str,
) -> None:
    if success:
        st.success(
            "Operation completed successfully."
        )
    else:
        st.error(
            "Operation failed."
        )

    if output:
        with st.expander(
            "Execution log",
            expanded=not success,
        ):
            st.code(
                output,
                language="text",
            )


# ============================================================
# OVERVIEW
# ============================================================

def _render_overview() -> None:
    st.subheader(
        "Platform Health"
    )

    db_ok, db_message = (
        _database_health()
    )

    propagation = (
        _customer_propagation()
    )

    pbix = _find_powerbi_file()
    excel = _find_excel_report()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        _status_card(
            "PostgreSQL",
            (
                "ONLINE"
                if db_ok
                else "ERROR"
            ),
            db_message,
        )

    with c2:
        _status_card(
            "Customer Pipeline",
            (
                "SYNCED"
                if propagation[
                    "synchronized"
                ]
                else "CHECK"
            ),
            (
                "RAW → Staging → Warehouse "
                "→ Analytics"
            ),
        )

    with c3:
        _status_card(
            "Power BI",
            (
                "AVAILABLE"
                if pbix
                else "NOT FOUND"
            ),
            (
                pbix.name
                if pbix
                else (
                    "No PBIX/PBIT "
                    "artifact detected"
                )
            ),
        )

    with c4:
        _status_card(
            "Excel BI",
            (
                "AVAILABLE"
                if excel
                else "NOT FOUND"
            ),
            (
                excel.name
                if excel
                else (
                    "No XLSX "
                    "artifact detected"
                )
            ),
        )

    st.divider()

    st.subheader(
        "Customer Propagation"
    )

    counts = propagation["counts"]

    cols = st.columns(4)

    for column, label in zip(
        cols,
        (
            "RAW",
            "STAGING",
            "WAREHOUSE",
            "ANALYTICS",
        ),
    ):
        with column:
            value = counts.get(
                label
            )

            st.metric(
                label,
                (
                    f"{value:,}"
                    if value is not None
                    else "ERROR"
                ),
            )

    if propagation["synchronized"]:
        st.success(
            "Customer data is synchronized "
            "end-to-end."
        )
    else:
        st.error(
            "Customer propagation is not "
            "fully synchronized."
        )

        for error in propagation[
            "errors"
        ]:
            st.caption(error)

    st.divider()

    st.subheader(
        "RAW Platform Volume"
    )

    st.dataframe(
        _platform_counts(),
        width="stretch",
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Analytics Semantic Layer"
    )

    st.dataframe(
        [
            _view_status(view)
            for view in ADMIN_MONITOR_VIEWS
        ],
        width="stretch",
        hide_index=True,
    )


# ============================================================
# DATA OPERATIONS
# ============================================================

def _render_data_operations() -> None:
    st.subheader(
        "Data Operations"
    )

    st.info(
        "The Admin UI exposes only approved Nexus360 "
        "operations. Arbitrary SQL and shell execution "
        "are intentionally unavailable."
    )

    st.markdown(
        "### One-Click Platform Update"
    )

    st.write(
        "Generate a new incremental enterprise batch and "
        "run the canonical Nexus360 pipeline through RAW, "
        "staging, warehouse, analytics, ML and Excel."
    )

    customers = st.number_input(
        "New customers to generate",
        min_value=1,
        max_value=1000,
        value=25,
        step=1,
        key="admin_incremental_customers",
    )

    confirm = st.checkbox(
        (
            "I confirm that I want to append "
            "a new enterprise-data batch."
        ),
        key="admin_confirm_platform_update",
    )

    if st.button(
        "Generate + Update Nexus360",
        type="primary",
        width="stretch",
        disabled=not confirm,
        key="admin_run_full_pipeline",
    ):
        with st.spinner(
            "Running the Nexus360 end-to-end pipeline..."
        ):
            success, output = (
                _run_platform_pipeline(
                    int(customers)
                )
            )

        _render_operation_result(
            success,
            output,
        )

    st.divider()

    st.markdown(
        "### Refresh Existing Data"
    )

    st.write(
        "Do not generate new customers. Propagate the "
        "existing RAW data through staging, warehouse, "
        "analytics, current churn scoring and Excel."
    )

    refresh_confirm = st.checkbox(
        (
            "I confirm that I want to refresh "
            "existing platform data."
        ),
        key="admin_confirm_refresh_only",
    )

    if st.button(
        "Refresh Existing Data Only",
        width="stretch",
        disabled=not refresh_confirm,
        key="admin_refresh_existing",
    ):
        with st.spinner(
            "Refreshing existing Nexus360 data..."
        ):
            success, output = (
                _run_refresh_only()
            )

        _render_operation_result(
            success,
            output,
        )

    st.divider()

    st.markdown(
        "### External Intelligence Refresh"
    )

    st.write(
        "Refresh approved external intelligence sources "
        "such as World Bank, Open-Meteo and Frankfurter. "
        "This operation does not generate synthetic customers."
    )

    if st.button(
        "Refresh External API Data",
        width="stretch",
        key="admin_external_refresh",
    ):
        with st.spinner(
            "Refreshing external intelligence..."
        ):
            success, output = (
                _run_python_script(
                    EXTERNAL_INGEST_SCRIPT,
                    timeout=UTILITY_TIMEOUT,
                )
            )

        if success:
            clear_dashboard_cache()

        _render_operation_result(
            success,
            output,
        )


# ============================================================
# REPORTS / POWER BI
# ============================================================

def _render_reports() -> None:
    st.subheader(
        "Reports & Power BI"
    )

    pbix = _find_powerbi_file()
    excel = _find_excel_report()

    st.markdown(
        "### Power BI"
    )

    if pbix:
        stat = pbix.stat()

        st.success(
            f"Detected: {pbix.name}"
        )

        st.caption(
            f"Last modified: "
            f"{_format_timestamp(stat.st_mtime)}"
        )

        st.caption(
            f"Size: "
            f"{stat.st_size / (1024 * 1024):.2f} MB"
        )

        c1, c2 = st.columns(2)

        with c1:
            st.download_button(
                "Download Power BI File",
                data=_read_binary(pbix),
                file_name=pbix.name,
                mime=(
                    "application/"
                    "octet-stream"
                ),
                width="stretch",
                key="admin_download_pbix",
            )

        with c2:
            if st.button(
                "Open Power BI File",
                width="stretch",
                key="admin_open_pbix",
            ):
                success, message = (
                    _open_local_file(
                        pbix
                    )
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

        st.warning(
            "The Nexus360 pipeline updates PostgreSQL and "
            "the analytical source used by Power BI. "
            "Opening/downloading the PBIX does not itself "
            "refresh the Power BI model. If the PBIX uses "
            "Import mode, refresh it in Power BI Desktop "
            "or configure a Power BI Service refresh. "
            "DirectQuery reports query PostgreSQL according "
            "to their configured connection."
        )

    else:
        st.warning(
            "No Power BI PBIX/PBIT artifact "
            "was detected."
        )

    st.divider()

    st.markdown(
        "### Excel Executive Report"
    )

    if excel:
        stat = excel.stat()

        st.success(
            f"Detected: {excel.name}"
        )

        st.caption(
            f"Last modified: "
            f"{_format_timestamp(stat.st_mtime)}"
        )

        st.download_button(
            "Download Latest Excel Report",
            data=_read_binary(excel),
            file_name=excel.name,
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            width="stretch",
            key="admin_download_excel",
        )

    else:
        st.warning(
            "No Excel report was detected."
        )

    if st.button(
        "Regenerate Excel Report",
        width="stretch",
        key="admin_regenerate_excel",
    ):
        with st.spinner(
            "Generating Excel executive report..."
        ):
            success, output = (
                _run_python_script(
                    EXCEL_REPORT_SCRIPT,
                    timeout=UTILITY_TIMEOUT,
                )
            )

        _render_operation_result(
            success,
            output,
        )


# ============================================================
# EXTERNAL API CENTER
# ============================================================

def _render_api_center() -> None:
    st.subheader(
        "External Intelligence"
    )

    st.info(
        "Nexus360 uses approved external data ingestion "
        "for macroeconomic, weather and FX intelligence. "
        "The ingestion script may use cached responses "
        "when available; therefore a successful ingestion "
        "run does not necessarily mean every record was "
        "downloaded live during that run."
    )

    rows = [
        {
            "Provider": "World Bank",
            "Purpose": (
                "GDP, population, internet usage, "
                "inflation and macroeconomic context"
            ),
            "Mode": "API / cache-aware ingestion",
        },
        {
            "Provider": "Open-Meteo",
            "Purpose": (
                "Historical weather intelligence "
                "for cloud operations"
            ),
            "Mode": "API / cache-aware ingestion",
        },
        {
            "Provider": "Frankfurter",
            "Purpose": (
                "Foreign-exchange reference rates"
            ),
            "Mode": "API / cache-aware ingestion",
        },
    ]

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "Use Data Operations → Refresh External API Data "
        "to run the approved ingestion workflow."
    )


# ============================================================
# APPLICATION MAP
# ============================================================

def _render_navigation() -> None:
    st.subheader(
        "Application Map"
    )

    st.write(
        "Use the application's main navigation to move "
        "between Nexus360 analytical domains."
    )

    rows = [
        {
            "Area": label,
            "Context": page,
        }
        for label, page
        in NAVIGATION_TARGETS
    ]

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )

    st.info(
        "Navigation is intentionally delegated to the "
        "main Nexus360 application router so the Admin "
        "page does not duplicate or bypass app-level "
        "routing logic."
    )


# ============================================================
# SYSTEM
# ============================================================

def _render_system_info() -> None:
    st.subheader(
        "System Information"
    )

    db_ok, db_message = (
        _database_health()
    )

    propagation = (
        _customer_propagation()
    )

    info = {
        "Project Root": str(
            PROJECT_ROOT
        ),
        "Python": sys.version.split()[0],
        "Python Executable": (
            sys.executable
        ),
        "Canonical Pipeline": str(
            PIPELINE_SCRIPT
        ),
        "Pipeline Exists": (
            PIPELINE_SCRIPT.exists()
        ),
        "PostgreSQL": (
            "Online"
            if db_ok
            else "Error"
        ),
        "Customer Pipeline": (
            "Synchronized"
            if propagation[
                "synchronized"
            ]
            else "Not synchronized"
        ),
    }

    for key, value in info.items():
        st.text(
            f"{key}: {value}"
        )

    st.caption(
        db_message
    )

    st.divider()

    st.markdown(
        "### Architecture"
    )

    st.code(
        """
Incremental Generator
        |
        v
Incremental RAW Loader
        |
        v
PostgreSQL RAW
        |
        v
Staging
        |
        v
Warehouse Dimensions / Facts
        |
        v
Analytics Semantic Layer
       / | \
      /  |  \
     v   v   v
Streamlit   ML / AI   Excel
     |
     v
Grounded Nexus360 Copilot

PostgreSQL Analytics
        |
        v
Power BI
(configured report refresh / DirectQuery behavior applies)
        """.strip(),
        language="text",
    )


# ============================================================
# PAGE
# ============================================================

def render() -> None:
    _render_admin_css()

    render_page_header(
        title="Admin Control Center",
        subtitle=(
            "Govern Nexus360 data operations, external "
            "intelligence, analytics health, BI artifacts, "
            "ML refresh and platform administration "
            "from one place."
        ),
        eyebrow=(
            "NEXUS 360 • PLATFORM OPERATIONS"
        ),
    )

    st.warning(
        "Administrator controls can modify analytical "
        "data. Incremental generation is append-only. "
        "Review the execution log if a pipeline operation "
        "fails before running another update."
    )

    (
        overview,
        data,
        reports,
        api,
        navigation,
        system,
    ) = st.tabs(
        [
            "Overview",
            "Data Operations",
            "Reports & Power BI",
            "External APIs",
            "Application Map",
            "System",
        ]
    )

    with overview:
        _render_overview()

    with data:
        _render_data_operations()

    with reports:
        _render_reports()

    with api:
        _render_api_center()

    with navigation:
        _render_navigation()

    with system:
        _render_system_info()