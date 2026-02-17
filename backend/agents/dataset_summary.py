from __future__ import annotations

from typing import Any

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import (
    build_dataset_summary_system_prompt,
    build_dataset_summary_user_prompt,
)
from backend.core.state import ColumnRole, DatasetProfile, DatasetSummaryReport, DomainClassification


class DatasetSummaryAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self.llm_client.register_fallback(DatasetSummaryReport, self._fallback_summary)
        self._fallback_profile: DatasetProfile | None = None
        self._fallback_domain: DomainClassification | None = None
        self._include_analysis_guidance: bool = False

    async def generate(
        self,
        profile: DatasetProfile,
        domain_classification: DomainClassification,
        include_analysis_guidance: bool = False,
    ) -> DatasetSummaryReport:
        self._fallback_profile = profile
        self._fallback_domain = domain_classification
        self._include_analysis_guidance = include_analysis_guidance
        llm_context = self._build_llm_context(profile)
        return await self.llm_client.generate_structured(
            system_prompt=build_dataset_summary_system_prompt(),
            user_prompt=build_dataset_summary_user_prompt(
                llm_context=llm_context,
                domain_payload=domain_classification.model_dump(),
                analysis_guidance_enabled=include_analysis_guidance,
            ),
            response_model=DatasetSummaryReport,
            temperature=0.2,
        )

    def _build_llm_context(self, profile: DatasetProfile) -> dict[str, Any]:
        roles = profile.column_roles
        metric_columns = [name for name, role in roles.items() if role == ColumnRole.NUMERIC_METRIC]
        dimension_columns = [name for name, role in roles.items() if role == ColumnRole.CATEGORICAL_DIMENSION]
        datetime_columns = [name for name, role in roles.items() if role == ColumnRole.DATETIME]
        identifier_columns = [name for name, role in roles.items() if role == ColumnRole.IDENTIFIER]
        high_missing_columns = [
            {"column": name, "missing_percentage": pct}
            for name, pct in profile.missing_percentage.items()
            if pct > 10
        ]

        metric_ranges: dict[str, dict[str, float | None]] = {}
        for column in metric_columns:
            summary = profile.column_summary.get(column, {})
            metric_ranges[column] = {
                "min": self._as_float(summary.get("min")),
                "max": self._as_float(summary.get("max")),
                "mean": self._as_float(summary.get("mean")),
                "std": self._as_float(summary.get("std")),
            }

        top_categories: dict[str, dict[str, str | int | None]] = {}
        for column in dimension_columns[:15]:
            summary = profile.column_summary.get(column, {})
            top_categories[column] = {
                "top_value": self._as_str(summary.get("top_value")),
                "top_frequency": self._as_int(summary.get("top_frequency")),
                "unique_count": self._as_int(summary.get("unique_count")),
            }

        return {
            "dataset_shape": {
                "total_rows": profile.total_rows,
                "total_columns": profile.total_columns,
            },
            "metric_columns": metric_columns,
            "dimension_columns": dimension_columns,
            "datetime_columns": datetime_columns,
            "identifier_columns": identifier_columns,
            "high_missing_columns": high_missing_columns,
            "duplicate_rows": profile.duplicate_rows,
            "metric_ranges": metric_ranges,
            "top_categories": top_categories,
        }

    @staticmethod
    def _as_float(value: Any) -> float | None:
        return float(value) if isinstance(value, (int, float)) else None

    @staticmethod
    def _as_int(value: Any) -> int | None:
        return int(value) if isinstance(value, (int, float)) else None

    @staticmethod
    def _as_str(value: Any) -> str | None:
        return str(value) if value is not None else None

    async def _fallback_summary(self, _system_prompt: str, _user_prompt: str) -> dict:
        if self._fallback_profile is None or self._fallback_domain is None:
            return {
                "executive_summary": "Dataset summary unavailable because metadata context is missing.",
                "data_health_assessment": "Unable to assess data health without profile metadata.",
                "statistical_highlights": ["No statistical highlights available."],
                "anomaly_indicators": ["No anomaly indicators available."],
                "recommended_starting_points": ["Re-run upload and profiling to regenerate metadata context."],
                "important_features": [],
                "useful_statistics": [],
                "confidence": 0.2,
            }

        profile = self._fallback_profile
        domain = self._fallback_domain
        roles = profile.column_roles
        metric_columns = [name for name, role in roles.items() if role == ColumnRole.NUMERIC_METRIC]
        identifier_columns = [name for name, role in roles.items() if role == ColumnRole.IDENTIFIER]
        missing_over_10 = [col for col, pct in profile.missing_percentage.items() if pct > 10]
        max_missing_col = max(profile.missing_percentage, key=profile.missing_percentage.get, default=None)
        max_missing_pct = profile.missing_percentage.get(max_missing_col, 0.0) if max_missing_col else 0.0

        spread_signals: list[str] = []
        for col in metric_columns:
            summary = profile.column_summary.get(col, {})
            min_v = summary.get("min")
            max_v = summary.get("max")
            std_v = summary.get("std")
            if isinstance(min_v, (int, float)) and isinstance(max_v, (int, float)):
                spread_signals.append(
                    f"{col} spans from {round(float(min_v), 3)} to {round(float(max_v), 3)}."
                )
            if isinstance(std_v, (int, float)) and float(std_v) > 0:
                spread_signals.append(f"{col} has standard deviation {round(float(std_v), 3)}.")
            if len(spread_signals) >= 3:
                break

        statistical_highlights = [
            f"Dataset contains {profile.total_rows} rows across {profile.total_columns} columns.",
            (
                f"Role mix: {len(metric_columns)} metric, "
                f"{len(profile.categorical_columns)} dimensions, "
                f"{len(profile.datetime_columns)} datetime, "
                f"{len(identifier_columns)} identifiers."
            ),
        ]
        statistical_highlights.extend(spread_signals[:3] or ["Numeric spread signals are limited from available summaries."])

        anomaly_indicators: list[str] = []
        if profile.duplicate_rows > 0:
            anomaly_indicators.append(f"{profile.duplicate_rows} duplicate rows detected, indicating integrity risk.")
        if missing_over_10:
            anomaly_indicators.append(
                f"Missingness above 10% in {len(missing_over_10)} columns: {', '.join(missing_over_10[:5])}."
            )
        if max_missing_col and max_missing_pct > 0:
            anomaly_indicators.append(
                f"Highest missingness is {round(max_missing_pct, 2)}% in column '{max_missing_col}'."
            )
        if not anomaly_indicators:
            anomaly_indicators.append("No critical anomaly signals detected from duplicates and missingness checks.")

        data_health_parts = []
        if profile.duplicate_rows > 0:
            data_health_parts.append("Duplicate rows require deduplication before deeper analysis.")
        if missing_over_10:
            data_health_parts.append("Several columns exceed 10% missingness and need imputation strategy.")
        if identifier_columns and len(identifier_columns) >= max(1, profile.total_columns // 2):
            data_health_parts.append("Identifier-heavy structure suggests a lookup or reference-oriented table.")
        if not data_health_parts:
            data_health_parts.append("Core health signals are stable with low duplicates and manageable missingness.")
        data_health_assessment = " ".join(data_health_parts)

        starting_points = [
            f"Start with domain-oriented KPI baselining for {domain.domain_label}.",
            "Run segmented summaries on dimension columns against key metric columns.",
        ]
        if profile.datetime_columns:
            starting_points.append(
                f"Build trend views over datetime field(s): {', '.join(profile.datetime_columns[:3])}."
            )
        if profile.potential_primary_keys:
            starting_points.append(
                f"Use likely identifier(s) {', '.join(profile.potential_primary_keys[:3])} for record-level tracing."
            )
        if missing_over_10:
            starting_points.append("Prioritize missing-data treatment before diagnostic or predictive workflows.")

        executive_summary = (
            f"This dataset is best described as {domain.domain_label.lower()} data with "
            f"{profile.total_rows} rows and {profile.total_columns} columns. "
            f"It includes {len(metric_columns)} measurable metric column(s) and "
            f"{len(profile.datetime_columns)} time-oriented column(s)."
        )
        important_features: list[str] = []
        useful_statistics: list[str] = []
        if getattr(self, "_include_analysis_guidance", False):
            important_features.extend(metric_columns[:6])
            important_features.extend(profile.datetime_columns[:2])
            important_features.extend(profile.categorical_columns[:4])
            important_features = list(dict.fromkeys([item for item in important_features if item]))[:10]

            if metric_columns:
                useful_statistics.append("Distribution summary (mean, median, std, range) for key metric columns.")
                useful_statistics.append("Outlier checks using IQR or z-score on high-variance metrics.")
            if profile.categorical_columns:
                useful_statistics.append("Category-level frequency and concentration analysis for segment columns.")
            if metric_columns and profile.categorical_columns:
                useful_statistics.append("Group-wise comparison (ANOVA or Kruskal) between dimensions and metrics.")
            if profile.datetime_columns and metric_columns:
                useful_statistics.append("Time-series trend and seasonality checks for datetime-linked metrics.")

        return {
            "executive_summary": executive_summary,
            "data_health_assessment": data_health_assessment,
            "statistical_highlights": statistical_highlights[:5],
            "anomaly_indicators": anomaly_indicators[:5],
            "recommended_starting_points": starting_points[:5],
            "important_features": important_features[:10],
            "useful_statistics": useful_statistics[:8],
            "confidence": 0.7,
        }
