from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import (
    build_phase6_intent_parser_system_prompt,
    build_phase6_intent_parser_user_prompt,
)
from backend.core.state import DatasetProfile, ParsedIntent


class IntentParserAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self._user_message: str = ""
        self._profile: DatasetProfile | None = None
        self.llm_client.register_fallback(ParsedIntent, self._fallback_intent)

    async def parse(self, user_message: str, dataset_profile: DatasetProfile) -> ParsedIntent:
        self._user_message = user_message
        self._profile = dataset_profile
        return await self.llm_client.generate_structured(
            system_prompt=build_phase6_intent_parser_system_prompt(),
            user_prompt=build_phase6_intent_parser_user_prompt(user_message, dataset_profile),
            response_model=ParsedIntent,
            temperature=0.0,
        )

    async def _fallback_intent(self, _system_prompt: str, _user_prompt: str) -> dict:
        profile = self._profile
        message = self._user_message.lower()
        if profile is None:
            return {
                "intent_type": "DIAGNOSTIC",
                "target_candidates": [],
                "requires_target": True,
                "reasoning": "Profile unavailable; defaulted to diagnostic intent requiring target.",
            }

        if any(term in message for term in ["predict", "forecast", "probability", "likely"]):
            intent_type = "PREDICTIVE"
        elif any(term in message for term in ["why", "reason", "driver", "cause", "influence"]):
            intent_type = "EXPLANATORY"
        elif any(term in message for term in ["compare", "difference", "segment", "breakdown"]):
            intent_type = "DIAGNOSTIC"
        else:
            intent_type = "DESCRIPTIVE"

        candidates = [column for column in profile.column_summary.keys() if column.lower() in message]

        keyword_hints = ["status", "approved", "default", "churn", "label", "outcome", "revenue", "income", "score", "amount", "risk"]
        if not candidates:
            for column in profile.column_summary.keys():
                column_l = column.lower()
                if any(hint in column_l for hint in keyword_hints):
                    candidates.append(column)

        return {
            "intent_type": intent_type,
            "target_candidates": candidates[:5],
            "requires_target": True,
            "reasoning": "Rule-based parsing from intent keywords and column-name matches.",
        }
