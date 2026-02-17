from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import build_driver_insight_system_prompt, build_driver_insight_user_prompt
from backend.core.state import DriverInsightReport, DriverRanking, IntentType, StatisticalResult


class InsightSynthesisAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self.llm_client.register_fallback(DriverInsightReport, self._fallback_report)
        self._ranking: DriverRanking | None = None
        self._intent_type: IntentType | None = None
        self._sample_size: int = 0
        self._target_variable: str | None = None

    async def synthesize(
        self,
        ranked_drivers: DriverRanking,
        intent_type: IntentType,
        sample_size: int,
        target_variable: str | None,
    ) -> DriverInsightReport:
        self._ranking = ranked_drivers
        self._intent_type = intent_type
        self._sample_size = sample_size
        self._target_variable = target_variable

        payload = {
            "ranked_drivers": [item.model_dump() for item in ranked_drivers.ranked_drivers],
            "intent_type": intent_type.value,
            "sample_size": sample_size,
            "target_variable": target_variable,
        }
        return await self.llm_client.generate_structured(
            system_prompt=build_driver_insight_system_prompt(),
            user_prompt=build_driver_insight_user_prompt(payload),
            response_model=DriverInsightReport,
            temperature=0.2,
        )

    async def _fallback_report(self, _system_prompt: str, _user_prompt: str) -> dict:
        if self._ranking is None or not self._ranking.ranked_drivers:
            return {
                "executive_driver_summary": "No statistically ranked drivers were identified from the executed tests.",
                "top_3_drivers": [],
                "strength_assessment": "Driver strength is currently low due to insufficient statistical evidence.",
                "recommended_next_step": "Collect more complete target/predictor observations and rerun analysis.",
                "confidence": 0.3,
            }

        top = self._ranking.ranked_drivers[:3]
        top_names = [f"{item.predictor} -> {item.target or 'n/a'}" for item in top]
        strongest = top[0]
        summary = (
            f"Top driver is {strongest.predictor} for target {strongest.target or 'n/a'} "
            f"based on {strongest.test_type} score {round(strongest.score, 4)}."
        )
        if strongest.p_value is not None:
            summary += f" Reported p-value is {round(strongest.p_value, 6)}."

        strength = "Moderate"
        if strongest.effect_size is not None and abs(strongest.effect_size) >= 0.5:
            strength = "Strong"
        elif strongest.effect_size is not None and abs(strongest.effect_size) < 0.15:
            strength = "Weak"

        return {
            "executive_driver_summary": summary,
            "top_3_drivers": top_names,
            "strength_assessment": (
                f"{strength} evidence from ranked statistical tests with sample size {self._sample_size}."
            ),
            "recommended_next_step": (
                "Validate the top driver on a holdout segment and then test interactions with secondary drivers."
            ),
            "confidence": 0.72 if self._sample_size >= 100 else 0.58,
        }
