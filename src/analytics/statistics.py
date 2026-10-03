from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy import stats


class StatisticalAnalyzer:

    @staticmethod
    def correlation_matrix(
        df: pd.DataFrame,
        method: Literal["pearson", "kendall", "spearman"] = "pearson",
    ) -> pd.DataFrame:

        numeric = df.select_dtypes(include=np.number)

        if numeric.empty:
            return pd.DataFrame()

        return numeric.corr(method=method)

    @staticmethod
    def pearson_test(
        df: pd.DataFrame,
        x: str,
        y: str,
    ) -> dict[str, float | int | None]:

        clean = (
            df[[x, y]]
            .apply(pd.to_numeric, errors="coerce")
            .dropna()
        )

        if len(clean) < 3:
            return {
                "n": len(clean),
                "correlation": None,
                "p_value": None,
            }

        if (
            clean[x].nunique() < 2
            or clean[y].nunique() < 2
        ):
            return {
                "n": len(clean),
                "correlation": None,
                "p_value": None,
            }

        result = stats.pearsonr(
            clean[x].to_numpy(dtype=float),
            clean[y].to_numpy(dtype=float),
        )

        return {
            "n": len(clean),
            "correlation": float(result.statistic),
            "p_value": float(result.pvalue),
        }

    @staticmethod
    def spearman_test(
        df: pd.DataFrame,
        x: str,
        y: str,
    ) -> dict[str, float | int | None]:

        clean = (
            df[[x, y]]
            .apply(pd.to_numeric, errors="coerce")
            .dropna()
        )

        if len(clean) < 3:
            return {
                "n": len(clean),
                "correlation": None,
                "p_value": None,
            }

        correlation, p_value = stats.spearmanr(
            clean[x],
            clean[y],
        )

        return {
            "n": len(clean),
            "correlation": float(correlation),
            "p_value": float(p_value),
        }

    @staticmethod
    def iqr_outliers(
        series: pd.Series,
    ) -> pd.Series:

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        )

        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)

        iqr = q3 - q1

        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)

        return (numeric < lower) | (numeric > upper)

    @staticmethod
    def z_scores(
        series: pd.Series,
    ) -> pd.Series:

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        )

        valid = numeric.dropna()

        result = pd.Series(
            np.nan,
            index=series.index,
            dtype=float,
        )

        if len(valid) < 2:
            return result

        std = valid.std(ddof=0)

        if std == 0:
            result.loc[valid.index] = 0.0
            return result

        result.loc[valid.index] = (
            valid - valid.mean()
        ) / std

        return result

    @staticmethod
    def confidence_interval_mean(
        series: pd.Series,
        confidence: float = 0.95,
    ) -> dict[str, Any]:

        clean = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        n = len(clean)

        if n < 2:
            return {
                "n": n,
                "mean": None,
                "lower": None,
                "upper": None,
            }

        mean = clean.mean()

        sem = stats.sem(clean)

        margin = stats.t.ppf(
            (1 + confidence) / 2,
            n - 1,
        ) * sem

        return {
            "n": n,
            "mean": float(mean),
            "lower": float(mean - margin),
            "upper": float(mean + margin),
        }