from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import (
    build_initial_insight_system_prompt,
    build_initial_insight_user_prompt,
)
from backend.core.state import DatasetProfile, DatasetSummaryReport, DomainClassification


class InitialInsightAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self.llm_client.register_fallback(DatasetSummaryReport, self._fallback_overview)
        self._fallback_profile: DatasetProfile | None = None
        self._fallback_domain: DomainClassification | None = None

    async def generate(
        self,
        profile: DatasetProfile,
        domain_classification: DomainClassification,
    ) -> DatasetSummaryReport:
        self._fallback_profile = profile
        self._fallback_domain = domain_classification
        return await self.llm_client.generate_structured(
            system_prompt=build_initial_insight_system_prompt(),
            user_prompt=build_initial_insight_user_prompt(
                profile=profile,
                domain_payload=domain_classification.model_dump(),
            ),
            response_model=DatasetSummaryReport,
        )

    async def _fallback_overview(self, _system_prompt: str, _user_prompt: str) -> dict:
        if self._fallback_profile is None or self._fallback_domain is None:
            return {
                "executive_summary": "Insufficient metadata for fallback overview.",
                "data_health_assessment": "Fallback executed without profile context.",
                "statistical_highlights": ["Load dataset and rerun profiling pipeline."],
                "anomaly_indicators": ["No anomaly assessment available."],
                "important_features": [],
                "useful_statistics": [],
                "confidence": 0.25,
            }

        profile = self._fallback_profile
        missing_cols = [col for col, pct in profile.missing_percentage.items() if pct > 0]
        high_missing_cols = [col for col, pct in profile.missing_percentage.items() if pct >= 20]

        quality_flags = []
        if profile.duplicate_rows > 0:
            quality_flags.append(f"{profile.duplicate_rows} duplicate rows detected.")
        if high_missing_cols:
            quality_flags.append(
                f"High missingness (>=20%) in {len(high_missing_cols)} columns: {', '.join(high_missing_cols[:5])}."
            )
        if not quality_flags:
            quality_flags.append("No major quality issues detected from deterministic profile checks.")

        directions = [
            "Analyze trends across key numeric features.",
            "Investigate relationships between categorical segments and numeric outcomes.",
            "Prioritize cleanup for columns with missing values before deeper modeling.",
        ]
        if profile.potential_primary_keys:
            directions.append(
                f"Use potential identifier(s) {', '.join(profile.potential_primary_keys[:3])} for record-level tracking."
            )

        anomaly_signals = []
        if profile.duplicate_rows > 0:
            anomaly_signals.append("Duplicate rows may indicate ingestion or upstream merge issues.")
        if high_missing_cols:
            anomaly_signals.append("Concentrated missingness may indicate process gaps in data capture.")
        if profile.total_rows > 0 and not anomaly_signals:
            anomaly_signals.append("No immediate anomaly signals from duplicate/missingness checks.")

        summary = (
            f"The dataset appears to be a {self._fallback_domain.domain_label.lower()} with "
            f"{profile.total_rows} rows and {profile.total_columns} columns. "
            f"It includes {len(profile.numeric_columns)} numeric, "
            f"{len(profile.categorical_columns)} categorical, and "
            f"{len(profile.datetime_columns)} datetime columns."
        )

        return {
            "executive_summary": summary,
            "data_health_assessment": quality_flags[0] if quality_flags else "No major quality flags.",
            "statistical_highlights": directions,
            "anomaly_indicators": anomaly_signals,
            "important_features": profile.numeric_columns[:6] + profile.categorical_columns[:4],
            "useful_statistics": [
                "Distribution summary for numeric metrics.",
                "Segment-level comparisons across categorical dimensions.",
            ],
            "confidence": 0.62,
        }
