from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import build_hypothesis_system_prompt, build_hypothesis_user_prompt
from backend.core.state import ColumnRole, DatasetProfile, Hypothesis, HypothesisSet, IntentClassification


class HypothesisGeneratorAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self.llm_client.register_fallback(HypothesisSet, self._fallback_hypotheses)
        self._profile: DatasetProfile | None = None
        self._intent: IntentClassification | None = None

    async def generate(
        self,
        intent_classification: IntentClassification,
        dataset_profile: DatasetProfile,
    ) -> HypothesisSet:
        self._profile = dataset_profile
        self._intent = intent_classification
        return await self.llm_client.generate_structured(
            system_prompt=build_hypothesis_system_prompt(),
            user_prompt=build_hypothesis_user_prompt(intent_classification, dataset_profile),
            response_model=HypothesisSet,
            temperature=0.2,
        )

    async def _fallback_hypotheses(self, _system_prompt: str, _user_prompt: str) -> dict:
        if self._profile is None:
            return {"hypotheses": []}

        profile = self._profile
        target = None
        if self._intent and self._intent.target_columns:
            for col in self._intent.target_columns:
                if col in profile.column_roles:
                    target = col
                    break

        metric_columns = [c for c, role in profile.column_roles.items() if role == ColumnRole.NUMERIC_METRIC]
        dimension_columns = [c for c, role in profile.column_roles.items() if role == ColumnRole.CATEGORICAL_DIMENSION]
        datetime_columns = [c for c, role in profile.column_roles.items() if role == ColumnRole.DATETIME]

        hypotheses: list[Hypothesis] = []
        if target and target in metric_columns:
            for predictor in metric_columns:
                if predictor == target:
                    continue
                hypotheses.append(
                    Hypothesis(
                        statement=f"{predictor} is associated with variation in {target}.",
                        predictor_column=predictor,
                        target_column=target,
                    )
                )
                if len(hypotheses) >= 3:
                    break

        if target and target in metric_columns and not hypotheses:
            for predictor in dimension_columns:
                hypotheses.append(
                    Hypothesis(
                        statement=f"Groups in {predictor} produce different average values of {target}.",
                        predictor_column=predictor,
                        target_column=target,
                    )
                )
                if len(hypotheses) >= 3:
                    break

        if not hypotheses and metric_columns:
            base_target = metric_columns[0]
            for predictor in metric_columns[1:4]:
                hypotheses.append(
                    Hypothesis(
                        statement=f"{predictor} has a measurable relationship with {base_target}.",
                        predictor_column=predictor,
                        target_column=base_target,
                    )
                )

        if not hypotheses and dimension_columns and metric_columns:
            hypotheses.append(
                Hypothesis(
                    statement=f"{dimension_columns[0]} segments explain changes in {metric_columns[0]}.",
                    predictor_column=dimension_columns[0],
                    target_column=metric_columns[0],
                )
            )

        if not hypotheses and datetime_columns and metric_columns:
            hypotheses.append(
                Hypothesis(
                    statement=f"Temporal progression in {datetime_columns[0]} influences {metric_columns[0]}.",
                    predictor_column=datetime_columns[0],
                    target_column=metric_columns[0],
                )
            )

        return {"hypotheses": [item.model_dump() for item in hypotheses[:5]]}
