from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.core.state import (
    ColumnRole,
    DatasetProfile,
    MissingValueSolution,
    MissingValueTreatmentResult,
)


class MissingValueTreatmentAgent:
    def suggest(self, profile: DatasetProfile) -> list[MissingValueSolution]:
        missing_columns = [col for col, pct in profile.missing_percentage.items() if pct > 0]
        if not missing_columns:
            return []

        high_missing_columns = [col for col, pct in profile.missing_percentage.items() if pct >= 40]
        numeric_columns = [col for col, role in profile.column_roles.items() if role == ColumnRole.NUMERIC_METRIC]
        categorical_columns = [
            col
            for col, role in profile.column_roles.items()
            if role in (ColumnRole.CATEGORICAL_DIMENSION, ColumnRole.BOOLEAN, ColumnRole.TEXT)
        ]
        datetime_columns = [col for col, role in profile.column_roles.items() if role == ColumnRole.DATETIME]

        solutions: list[MissingValueSolution] = [
            MissingValueSolution(
                solution_id="SMART_IMPUTE",
                title="Smart Imputation (Recommended)",
                description=(
                    "Fill numeric metrics with median, categorical/text fields with mode, "
                    "and datetime columns with forward/backward fill."
                ),
                action_type="SMART_IMPUTE",
                target_columns=missing_columns,
            )
        ]

        if high_missing_columns:
            solutions.append(
                MissingValueSolution(
                    solution_id="DROP_HIGH_MISSING_COLUMNS",
                    title="Drop High-Missing Columns",
                    description="Drop columns where missing percentage is 40% or higher.",
                    action_type="DROP_HIGH_MISSING_COLUMNS",
                    target_columns=high_missing_columns,
                )
            )

        if numeric_columns:
            solutions.append(
                MissingValueSolution(
                    solution_id="FILL_NUMERIC_MEDIAN",
                    title="Fill Numeric with Median",
                    description="Apply median fill for numeric metric columns only.",
                    action_type="FILL_NUMERIC_MEDIAN",
                    target_columns=[col for col in numeric_columns if col in missing_columns],
                )
            )
        if categorical_columns:
            solutions.append(
                MissingValueSolution(
                    solution_id="FILL_CATEGORICAL_MODE",
                    title="Fill Categorical/Text with Mode",
                    description="Apply mode fill for categorical and text-like columns.",
                    action_type="FILL_CATEGORICAL_MODE",
                    target_columns=[col for col in categorical_columns if col in missing_columns],
                )
            )
        if datetime_columns:
            solutions.append(
                MissingValueSolution(
                    solution_id="FILL_DATETIME_FFILL",
                    title="Fill Datetime with Forward/Backward Fill",
                    description="Propagate nearest valid datetime values forward then backward.",
                    action_type="FILL_DATETIME_FFILL",
                    target_columns=[col for col in datetime_columns if col in missing_columns],
                )
            )

        return [solution for solution in solutions if solution.target_columns]

    def apply(
        self,
        dataframe: pd.DataFrame,
        profile: DatasetProfile,
        solution: MissingValueSolution,
    ) -> tuple[pd.DataFrame, MissingValueTreatmentResult]:
        before_df = dataframe.copy()
        df = dataframe.copy()
        missing_before = int(df.isna().sum().sum())
        rows_before = int(df.shape[0])

        if solution.action_type == "SMART_IMPUTE":
            self._fill_numeric_median(df, profile)
            self._fill_categorical_mode(df, profile)
            self._fill_datetime(df, profile)
        elif solution.action_type == "DROP_HIGH_MISSING_COLUMNS":
            cols_to_drop = [col for col in solution.target_columns if col in df.columns]
            df = df.drop(columns=cols_to_drop)
        elif solution.action_type == "FILL_NUMERIC_MEDIAN":
            self._fill_numeric_median(df, profile)
        elif solution.action_type == "FILL_CATEGORICAL_MODE":
            self._fill_categorical_mode(df, profile)
        elif solution.action_type == "FILL_DATETIME_FFILL":
            self._fill_datetime(df, profile)
        else:
            raise ValueError(f"Unsupported missing-value action: {solution.action_type}")

        missing_after = int(df.isna().sum().sum())
        rows_after = int(df.shape[0])
        affected = [
            col for col in before_df.columns if col in df.columns and before_df[col].isna().sum() != df[col].isna().sum()
        ]
        if solution.action_type == "DROP_HIGH_MISSING_COLUMNS":
            affected = solution.target_columns

        result = MissingValueTreatmentResult(
            solution_id=solution.solution_id,
            applied=True,
            rows_before=rows_before,
            rows_after=rows_after,
            missing_before=missing_before,
            missing_after=missing_after,
            affected_columns=affected,
            summary=(
                f"{solution.title} applied. Missing values reduced from {missing_before} to {missing_after}."
            ),
        )
        return df, result

    @staticmethod
    def _fill_numeric_median(df: pd.DataFrame, profile: DatasetProfile) -> None:
        for column, role in profile.column_roles.items():
            if role == ColumnRole.NUMERIC_METRIC and column in df.columns and df[column].isna().any():
                median_value = df[column].median()
                if pd.isna(median_value):
                    median_value = 0
                df[column] = df[column].fillna(median_value)

    @staticmethod
    def _fill_categorical_mode(df: pd.DataFrame, profile: DatasetProfile) -> None:
        for column, role in profile.column_roles.items():
            if role in (ColumnRole.CATEGORICAL_DIMENSION, ColumnRole.BOOLEAN, ColumnRole.TEXT) and column in df.columns:
                if not df[column].isna().any():
                    continue
                mode = df[column].mode(dropna=True)
                fill_value = mode.iloc[0] if not mode.empty else "UNKNOWN"
                df[column] = df[column].fillna(fill_value)

    @staticmethod
    def _fill_datetime(df: pd.DataFrame, profile: DatasetProfile) -> None:
        for column, role in profile.column_roles.items():
            if role == ColumnRole.DATETIME and column in df.columns and df[column].isna().any():
                parsed = pd.to_datetime(df[column], errors="coerce")
                parsed = parsed.ffill().bfill()
                df[column] = parsed
