from __future__ import annotations

import pandas as pd


def check_required_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
) -> list[str]:

    return [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]


def count_nulls(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> int:

    return int(
        dataframe[
            columns
        ]
        .isna()
        .sum()
        .sum()
    )


def count_duplicates(
    dataframe: pd.DataFrame,
    key_columns: list[str],
) -> int:

    return int(
        dataframe.duplicated(
            subset=key_columns
        ).sum()
    )


def count_negative_values(
    dataframe: pd.DataFrame,
    column: str,
) -> int:

    return int(
        (
            dataframe[column]
            < 0
        ).sum()
    )


def validate_percentage(
    dataframe: pd.DataFrame,
    column: str,
    minimum: float = 0,
    maximum: float = 100,
) -> int:

    invalid = (
        (
            dataframe[column]
            < minimum
        )
        |
        (
            dataframe[column]
            > maximum
        )
    )

    return int(
        invalid.sum()
    )