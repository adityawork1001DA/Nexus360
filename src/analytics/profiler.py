from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class DataProfiler:
    """
    Nexus 360 enterprise data profiler.

    Handles:
    - integer columns
    - floating-point columns
    - PostgreSQL NUMERIC / Decimal values
    - boolean columns
    - nullable boolean columns
    - datetime columns
    - categorical/string columns
    - missing values
    - duplicate rows

    Boolean columns are intentionally excluded from percentile,
    mean, standard deviation, skewness and kurtosis calculations.
    """

    @staticmethod
    def _is_boolean(series: pd.Series) -> bool:
        """
        Return True for standard and nullable pandas boolean columns.
        """

        return bool(
            pd.api.types.is_bool_dtype(series.dtype)
        )

    @classmethod
    def _numeric_series(
        cls,
        series: pd.Series,
    ) -> pd.Series:
        """
        Convert a genuinely numeric series into float64.

        Boolean columns are explicitly rejected because NumPy
        quantile interpolation cannot safely subtract boolean values.
        """

        if cls._is_boolean(series):
            return pd.Series(
                dtype="float64"
            )

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        )

        return numeric.astype(
            "float64"
        ).dropna()

    @staticmethod
    def _safe_number(
        value: Any,
    ) -> float | None:
        """
        Convert NumPy/Pandas numeric values into JSON-safe floats.
        """

        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        try:
            numeric_value = float(value)
        except (TypeError, ValueError, OverflowError):
            return None

        if not np.isfinite(numeric_value):
            return None

        return round(
            numeric_value,
            6,
        )

    @staticmethod
    def _safe_scalar(
        value: Any,
    ) -> Any:
        """
        Convert common pandas/numpy scalar values into JSON-safe values.
        """

        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        if isinstance(
            value,
            (np.integer,),
        ):
            return int(value)

        if isinstance(
            value,
            (np.floating,),
        ):
            return float(value)

        if isinstance(
            value,
            (np.bool_,),
        ):
            return bool(value)

        if isinstance(
            value,
            (pd.Timestamp,),
        ):
            return value.isoformat()

        return value

    def profile(
        self,
        df: pd.DataFrame,
    ) -> dict[str, Any]:
        """
        Generate a complete data-quality and descriptive profile.
        """

        rows, columns = df.shape

        duplicate_rows = int(
            df.duplicated().sum()
        )

        total_cells = rows * columns

        missing_cells = int(
            df.isna().sum().sum()
        )

        missing_pct = (
            (missing_cells / total_cells) * 100
            if total_cells > 0
            else 0.0
        )

        column_profiles: dict[str, Any] = {}

        for column in df.columns:

            series = df[column]

            missing_count = int(
                series.isna().sum()
            )

            unique_count = int(
                series.nunique(
                    dropna=True
                )
            )

            column_data: dict[str, Any] = {
                "dtype": str(series.dtype),
                "missing_count": missing_count,
                "missing_pct": round(
                    float(
                        series.isna().mean()
                        * 100
                    ),
                    4,
                ),
                "unique_count": unique_count,
            }

            # -------------------------------------------------
            # BOOLEAN
            # -------------------------------------------------

            if self._is_boolean(series):

                true_count = int(
                    series.eq(True).sum()
                )

                false_count = int(
                    series.eq(False).sum()
                )

                valid_count = (
                    true_count
                    + false_count
                )

                column_data.update(
                    {
                        "column_type": "boolean",
                        "true_count": true_count,
                        "false_count": false_count,
                        "true_pct": round(
                            (
                                true_count
                                / valid_count
                                * 100
                            )
                            if valid_count > 0
                            else 0.0,
                            4,
                        ),
                        "false_pct": round(
                            (
                                false_count
                                / valid_count
                                * 100
                            )
                            if valid_count > 0
                            else 0.0,
                            4,
                        ),
                    }
                )

            # -------------------------------------------------
            # NUMERIC
            # -------------------------------------------------

            elif pd.api.types.is_numeric_dtype(
                series.dtype
            ):

                clean = self._numeric_series(
                    series
                )

                column_data[
                    "column_type"
                ] = "numeric"

                if not clean.empty:

                    column_data.update(
                        {
                            "min": self._safe_number(
                                clean.min()
                            ),
                            "max": self._safe_number(
                                clean.max()
                            ),
                            "mean": self._safe_number(
                                clean.mean()
                            ),
                            "median": self._safe_number(
                                clean.median()
                            ),
                            "std": self._safe_number(
                                clean.std()
                            ),
                            "q1": self._safe_number(
                                clean.quantile(
                                    0.25
                                )
                            ),
                            "q3": self._safe_number(
                                clean.quantile(
                                    0.75
                                )
                            ),
                            "p05": self._safe_number(
                                clean.quantile(
                                    0.05
                                )
                            ),
                            "p95": self._safe_number(
                                clean.quantile(
                                    0.95
                                )
                            ),
                        }
                    )

            # -------------------------------------------------
            # DATETIME
            # -------------------------------------------------

            elif pd.api.types.is_datetime64_any_dtype(
                series.dtype
            ):

                clean = series.dropna()

                column_data[
                    "column_type"
                ] = "datetime"

                if not clean.empty:

                    column_data.update(
                        {
                            "min": self._safe_scalar(
                                clean.min()
                            ),
                            "max": self._safe_scalar(
                                clean.max()
                            ),
                        }
                    )

            # -------------------------------------------------
            # TEXT / CATEGORY / OBJECT
            # -------------------------------------------------

            else:

                column_data[
                    "column_type"
                ] = "categorical"

                clean = series.dropna()

                if not clean.empty:

                    value_counts = (
                        clean.astype(str)
                        .value_counts()
                        .head(10)
                    )

                    column_data[
                        "top_values"
                    ] = {
                        str(key): int(value)
                        for key, value
                        in value_counts.items()
                    }

            column_profiles[
                str(column)
            ] = column_data

        return {
            "row_count": int(rows),
            "column_count": int(columns),
            "duplicate_rows": duplicate_rows,
            "duplicate_pct": round(
                (
                    duplicate_rows
                    / rows
                    * 100
                )
                if rows > 0
                else 0.0,
                4,
            ),
            "total_cells": int(
                total_cells
            ),
            "missing_cells": missing_cells,
            "missing_pct": round(
                missing_pct,
                4,
            ),
            "columns": column_profiles,
        }

    def numeric_summary(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Produce extended descriptive statistics.

        Boolean columns are explicitly excluded.
        """

        numeric_columns: list[str] = []

        for column in df.columns:

            series = df[column]

            if self._is_boolean(series):
                continue

            if pd.api.types.is_numeric_dtype(
                series.dtype
            ):
                numeric_columns.append(
                    column
                )

        if not numeric_columns:
            return pd.DataFrame()

        numeric = df[
            numeric_columns
        ].copy()

        for column in numeric.columns:

            numeric[column] = pd.to_numeric(
                numeric[column],
                errors="coerce",
            ).astype(
                "float64"
            )

        summary = numeric.describe(
            percentiles=[
                0.01,
                0.05,
                0.25,
                0.50,
                0.75,
                0.95,
                0.99,
            ]
        ).T

        summary["missing"] = (
            numeric.isna().sum()
        )

        summary["missing_pct"] = (
            numeric.isna().mean()
            * 100
        )

        summary["skew"] = (
            numeric.skew()
        )

        summary["kurtosis"] = (
            numeric.kurtosis()
        )

        summary["variance"] = (
            numeric.var()
        )

        summary["iqr"] = (
            summary["75%"]
            - summary["25%"]
        )

        return summary

    def missing_summary(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Column-level missing-value report.
        """

        result = pd.DataFrame(
            {
                "column": [
                    str(column)
                    for column
                    in df.columns
                ],
                "dtype": [
                    str(df[column].dtype)
                    for column
                    in df.columns
                ],
                "missing_count": [
                    int(
                        df[column]
                        .isna()
                        .sum()
                    )
                    for column
                    in df.columns
                ],
                "missing_pct": [
                    float(
                        df[column]
                        .isna()
                        .mean()
                        * 100
                    )
                    for column
                    in df.columns
                ],
                "unique_count": [
                    int(
                        df[column]
                        .nunique(
                            dropna=True
                        )
                    )
                    for column
                    in df.columns
                ],
            }
        )

        return (
            result.sort_values(
                [
                    "missing_pct",
                    "missing_count",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .reset_index(
                drop=True
            )
        )

    def boolean_summary(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Dedicated summary for boolean features.
        """

        records: list[dict[str, Any]] = []

        for column in df.columns:

            series = df[column]

            if not self._is_boolean(
                series
            ):
                continue

            true_count = int(
                series.eq(True).sum()
            )

            false_count = int(
                series.eq(False).sum()
            )

            missing_count = int(
                series.isna().sum()
            )

            valid_count = (
                true_count
                + false_count
            )

            records.append(
                {
                    "column": str(
                        column
                    ),
                    "true_count": (
                        true_count
                    ),
                    "false_count": (
                        false_count
                    ),
                    "missing_count": (
                        missing_count
                    ),
                    "true_pct": (
                        true_count
                        / valid_count
                        * 100
                        if valid_count > 0
                        else 0.0
                    ),
                }
            )

        return pd.DataFrame(
            records
        )

    def export_json(
        self,
        profile: dict[str, Any],
        path: str | Path,
    ) -> Path:
        """
        Export profiling output as formatted JSON.
        """

        output = Path(path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                profile,
                file,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        return output