from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import (
    build_intent_parser_system_prompt,
    build_intent_parser_user_prompt,
)
from backend.core.state import (
    DatasetProfile,
    DomainClassification,
    IntentClassification,
    IntentType,
)


class IntentParserAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self._profile: DatasetProfile | None = None
        self._domain: DomainClassification | None = None
        self._user_intent: str = ""
        self.llm_client.register_fallback(IntentClassification, self._fallback_intent)

    async def parse(
        self,
        user_intent: str,
        domain_classification: DomainClassification,
        dataset_profile: DatasetProfile,
    ) -> IntentClassification:
        self._profile = dataset_profile
        self._domain = domain_classification
        self._user_intent = user_intent
        return await self.llm_client.generate_structured(
            system_prompt=build_intent_parser_system_prompt(),
            user_prompt=build_intent_parser_user_prompt(
                user_intent=user_intent,
                domain=domain_classification,
                profile=dataset_profile,
            ),
            response_model=IntentClassification,
        )

    async def _fallback_intent(self, _system_prompt: str, _user_prompt: str) -> dict:
        intent_text = self._user_intent.lower()
        profile = self._profile
        columns = profile.column_summary.keys() if profile else []

        target_columns = [c for c in columns if c.lower() in intent_text]
        if not target_columns and profile:
            target_columns = list(profile.numeric_columns[:2] or profile.categorical_columns[:2])

        if any(k in intent_text for k in ["clean", "missing", "duplicate", "outlier"]):
            intent_type = IntentType.DATA_CLEANING
            explanation = "Detected cleaning keywords in user intent."
            confidence = 0.64
        elif any(k in intent_text for k in ["predict", "forecast", "model", "classification", "regression"]):
            intent_type = IntentType.PREDICTIVE
            explanation = "Detected predictive modeling keywords in user intent."
            confidence = 0.68
        elif any(k in intent_text for k in ["why", "cause", "driver", "correl", "variance", "compare"]):
            intent_type = IntentType.DIAGNOSTIC
            explanation = "Detected diagnostic/causal investigation keywords."
            confidence = 0.62
        else:
            intent_type = IntentType.DESCRIPTIVE
            explanation = "Defaulted to descriptive intent based on generic exploration phrasing."
            confidence = 0.56

        return {
            "intent_type": intent_type,
            "target_columns": target_columns,
            "explanation": explanation,
            "confidence": confidence,
        }
