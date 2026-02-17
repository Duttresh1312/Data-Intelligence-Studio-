from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import (
    build_domain_inference_system_prompt,
    build_domain_inference_user_prompt,
)
from backend.core.state import DatasetProfile, DomainClassification


class DomainInferenceAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self.llm_client.register_fallback(DomainClassification, self._fallback_domain)
        self._fallback_profile: DatasetProfile | None = None

    async def infer(
        self,
        profile: DatasetProfile,
        column_names: list[str],
    ) -> DomainClassification:
        self._fallback_profile = profile
        return await self.llm_client.generate_structured(
            system_prompt=build_domain_inference_system_prompt(),
            user_prompt=build_domain_inference_user_prompt(profile, column_names),
            response_model=DomainClassification,
        )

    async def _fallback_domain(self, _system_prompt: str, _user_prompt: str) -> dict:
        profile = self._fallback_profile
        if profile is None:
            return {
                "domain_label": "Structured Dataset",
                "confidence": 0.25,
                "reasoning": "Insufficient profile context was available for domain inference fallback.",
                "suggested_kpis": ["Missing Data Rate", "Duplicate Row Rate"],
            }

        metric_columns = [name for name, role in profile.column_roles.items() if role.value == "NUMERIC_METRIC"]
        datetime_columns = profile.datetime_columns
        identifier_columns = [name for name, role in profile.column_roles.items() if role.value == "IDENTIFIER"]
        if datetime_columns and metric_columns:
            label = "Operational Time-Series Dataset"
            reasoning = (
                f"Detected datetime column(s) {', '.join(datetime_columns[:2])} and "
                f"metric column(s) {', '.join(metric_columns[:2])}, indicating trend-ready operational data."
            )
            kpis = ["Trend Growth Rate", "Period-over-Period Change", "Data Completeness"]
            confidence = 0.58
        elif metric_columns:
            label = "Business Metrics Dataset"
            reasoning = (
                f"Detected measurable numeric metrics ({', '.join(metric_columns[:3])}) and "
                "categorical dimensions suitable for segmented KPI analysis."
            )
            kpis = ["Metric Distribution", "Segment Performance", "Duplicate Row Rate"]
            confidence = 0.52
        elif identifier_columns and len(identifier_columns) >= max(1, profile.total_columns // 2):
            label = "Reference or Lookup Dataset"
            reasoning = (
                "Identifier columns dominate the schema, which suggests a reference-oriented table "
                "rather than a metric-heavy analytical dataset."
            )
            kpis = ["Identifier Coverage", "Completeness by Field", "Duplicate Identifier Rate"]
            confidence = 0.49
        else:
            label = "Structured Dataset with Limited Domain Signals"
            reasoning = (
                "Available metadata contains limited metric/time signals, so domain confidence remains conservative."
            )
            kpis = ["Missing Data Rate", "Duplicate Row Rate", "Column Completeness"]
            confidence = 0.36

        return {
            "domain_label": label,
            "confidence": confidence,
            "reasoning": reasoning,
            "suggested_kpis": kpis,
        }
