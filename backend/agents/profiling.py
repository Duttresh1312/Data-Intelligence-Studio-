from __future__ import annotations

import warnings
from typing import Any, Dict, List

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)

from backend.core.state import ColumnRole, DatasetProfile


IDENTIFIER_NAME_HINTS = ("id", "uuid", "key", "code")


class ProfilingAgent:
    @staticmethod
    def _looks_like_datetime(series: pd.Series) -> bool:
        if is_datetime64_any_dtype(series):
            return True
        if is_numeric_dtype(series) or is_bool_dtype(series):
            return False
        non_null = series.dropna()
        if non_null.empty:
            return False
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(series, errors="coerce")
        valid_ratio = float(parsed.notna().sum()) / max(1, int(non_null.shape[0]))
        return valid_ratio >= 0.8

    @staticmethod
    def _is_identifier_name(column_name: str) -> bool:
        normalized = column_name.lower().replace(" ", "_")
        return any(hint in normalized for hint in IDENTIFIER_NAME_HINTS)

    def _detect_role(
        self,
        column: str,
        series: pd.Series,
        unique_count: int,
        total_rows: int,
        is_datetime_col: bool,
    ) -> ColumnRole:
        if unique_count == total_rows and total_rows > 0:
            return ColumnRole.IDENTIFIER
        if self._is_identifier_name(column):
            return ColumnRole.IDENTIFIER
        if is_datetime_col:
            return ColumnRole.DATETIME
        if is_bool_dtype(series):
            return ColumnRole.BOOLEAN
        if is_numeric_dtype(series):
            if unique_count < 10:
                return ColumnRole.CATEGORICAL_DIMENSION
            return ColumnRole.NUMERIC_METRIC
        if unique_count < 50:
            return ColumnRole.CATEGORICAL_DIMENSION
        return ColumnRole.TEXT

    def profile(self, dataframe: pd.DataFrame) -> DatasetProfile:
        df = dataframe.copy()
        total_rows, total_columns = df.shape

        numeric_columns: List[str] = []
        categorical_columns: List[str] = []
        datetime_columns: List[str] = []
        column_summary: Dict[str, Dict[str, Any]] = {}
        column_roles: Dict[str, ColumnRole] = {}

        for column in df.columns:
            series = df[column]
            non_null = series.dropna()
            unique_count = int(non_null.nunique())
            is_datetime_col = self._looks_like_datetime(series)
            role = self._detect_role(
                column=column,
                series=series,
                unique_count=unique_count,
                total_rows=total_rows,
                is_datetime_col=is_datetime_col,
            )
            column_roles[column] = role

            if role == ColumnRole.DATETIME:
                datetime_columns.append(column)
                mode = non_null.mode(dropna=True)
                top_freq = int(non_null.value_counts(dropna=True).iloc[0]) if not non_null.empty else 0
                column_summary[column] = {
                    "dtype": str(series.dtype),
                    "role": role.value,
                    "unique_count": unique_count,
                    "top_value": str(mode.iloc[0]) if not mode.empty else None,
                    "top_frequency": top_freq,
                }
                continue

            if role == ColumnRole.NUMERIC_METRIC:
                numeric_columns.append(column)
                column_summary[column] = {
                    "dtype": str(series.dtype),
                    "role": role.value,
                    "mean": float(series.mean()) if not non_null.empty else None,
                    "std": float(series.std()) if not non_null.empty else None,
                    "min": float(series.min()) if not non_null.empty else None,
                    "max": float(series.max()) if not non_null.empty else None,
                    "unique_count": unique_count,
                }
                continue

            if role in (ColumnRole.CATEGORICAL_DIMENSION, ColumnRole.BOOLEAN):
                categorical_columns.append(column)

            mode = non_null.mode(dropna=True)
            top_freq = int(non_null.value_counts(dropna=True).iloc[0]) if not non_null.empty else 0
            column_summary[column] = {
                "dtype": str(series.dtype),
                "role": role.value,
                "unique_count": unique_count,
                "top_value": str(mode.iloc[0]) if not mode.empty else None,
                "top_frequency": top_freq,
            }

        missing_percentage = {
            column: round(float(df[column].isna().mean() * 100.0), 2)
            for column in df.columns
        }
        duplicate_rows = int(df.duplicated().sum())

        potential_primary_keys: List[str] = []
        for column in df.columns:
            series = df[column]
            if series.isna().sum() == 0 and int(series.nunique(dropna=False)) == total_rows:
                potential_primary_keys.append(column)

        return DatasetProfile(
            total_rows=total_rows,
            total_columns=total_columns,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            datetime_columns=datetime_columns,
            missing_percentage=missing_percentage,
            duplicate_rows=duplicate_rows,
            potential_primary_keys=potential_primary_keys,
            column_roles=column_roles,
            column_summary=column_summary,
        )
