from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import (
    build_phase6_insight_synthesis_system_prompt,
    build_phase6_insight_synthesis_user_prompt,
)
from backend.core.state import DriverScore, FinalAnalysisAnswer, StatisticalResultBundle


class InsightSynthesisAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self.llm_client.register_fallback(FinalAnalysisAnswer, self._fallback)
        self._question: str = ""
        self._target_column: str = ""
        self._target_type: str = ""
        self._drivers: list[DriverScore] = []
        self._bundle: StatisticalResultBundle | None = None

    async def synthesize(
        self,
        user_question: str,
        target_column: str,
        target_type: str,
        ranked_drivers: list[DriverScore],
        statistical_summary: StatisticalResultBundle,
    ) -> FinalAnalysisAnswer:
        self._question = user_question
        self._target_column = target_column
        self._target_type = target_type
        self._drivers = ranked_drivers
        self._bundle = statistical_summary

        payload = {
            "user_question": user_question,
            "target_column": target_column,
            "target_type": target_type,
            "top_drivers": [driver.model_dump() for driver in ranked_drivers[:5]],
            "statistical_summary": statistical_summary.model_dump(),
            "model_type_used": statistical_summary.model_type_used,
            "data_quality_flags": statistical_summary.data_quality_flags,
        }

        return await self.llm_client.generate_structured(
            system_prompt=build_phase6_insight_synthesis_system_prompt(),
            user_prompt=build_phase6_insight_synthesis_user_prompt(payload),
            response_model=FinalAnalysisAnswer,
            temperature=0.2,
        )

    async def _fallback(self, _system_prompt: str, _user_prompt: str) -> dict:
        if not self._drivers or self._bundle is None:
            return {
                "direct_answer": "The system could not identify strong evidence-based drivers from the current dataset and target setup.",
                "key_drivers_summary": "No ranked drivers were produced.",
                "evidence_points": ["Insufficient statistical results after validation filters."],
                "business_impact": "Decision confidence remains low until stronger statistical signals are available.",
                "confidence_score": 0.32,
                "recommended_next_step": "Confirm target variable quality and increase usable sample size.",
            }

        strongest = self._drivers[0]
        evidence: list[str] = []
        for driver in self._drivers[:3]:
            parts = [f"{driver.feature} (strength {driver.strength_score:.2f})"]
            if driver.p_value is not None:
                parts.append(f"p={driver.p_value:.4f}")
            if driver.effect_size is not None:
                parts.append(f"effect={driver.effect_size:.3f}")
            if driver.feature_importance is not None:
                parts.append(f"importance={driver.feature_importance:.3f}")
            evidence.append(", ".join(parts))

        return {
            "direct_answer": (
                f"The strongest driver for {self._target_column} is {strongest.feature}, "
                f"supported by the highest combined statistical and model-based score ({strongest.strength_score:.2f})."
            ),
            "key_drivers_summary": (
                f"Top drivers are {', '.join(driver.feature for driver in self._drivers[:3])}. "
                f"These variables consistently rank high across significance and predictive contribution."
            ),
            "evidence_points": evidence,
            "business_impact": (
                "Prioritizing interventions on the top-ranked drivers is likely to create the fastest measurable movement in the target outcome."
            ),
            "confidence_score": max(0.45, min(0.95, strongest.strength_score)),
            "recommended_next_step": (
                f"Validate the effect of {strongest.feature} on {self._target_column} across key segments before operational rollout."
            ),
        }
