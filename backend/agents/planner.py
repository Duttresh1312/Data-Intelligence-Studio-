from __future__ import annotations

from backend.app.llm.client import LLMClient
from backend.app.llm.prompts import build_planner_system_prompt, build_planner_user_prompt
from backend.core.state import (
    AnalysisPlan,
    DatasetProfile,
    IntentClassification,
    IntentType,
    OperationType,
    PlanStep,
)


class AnalysisPlannerAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()
        self._intent: IntentClassification | None = None
        self._profile: DatasetProfile | None = None
        self.llm_client.register_fallback(AnalysisPlan, self._fallback_plan)

    async def plan(
        self,
        intent_classification: IntentClassification,
        dataset_profile: DatasetProfile,
    ) -> AnalysisPlan:
        self._intent = intent_classification
        self._profile = dataset_profile
        return await self.llm_client.generate_structured(
            system_prompt=build_planner_system_prompt(),
            user_prompt=build_planner_user_prompt(
                intent=intent_classification,
                profile=dataset_profile,
            ),
            response_model=AnalysisPlan,
        )

    async def _fallback_plan(self, _system_prompt: str, _user_prompt: str) -> dict:
        intent = self._intent
        profile = self._profile
        if not intent or not profile:
            return {
                "intent_type": IntentType.DESCRIPTIVE,
                "steps": [
                    {
                        "step_id": "step_1",
                        "description": "Generate summary statistics.",
                        "operation_type": OperationType.SUMMARY,
                        "parameters": {},
                    }
                ],
            }

        steps: list[PlanStep] = []

        def add(step_id: str, description: str, op: OperationType, parameters: dict) -> None:
            steps.append(
                PlanStep(
                    step_id=step_id,
                    description=description,
                    operation_type=op,
                    parameters=parameters,
                )
            )

        if intent.intent_type == IntentType.DESCRIPTIVE:
            add("step_1", "Generate dataset summary statistics.", OperationType.SUMMARY, {})
            if profile.categorical_columns and profile.numeric_columns:
                add(
                    "step_2",
                    "Compare numeric outcome by primary category.",
                    OperationType.GROUPBY,
                    {
                        "group_by": profile.categorical_columns[0],
                        "target_column": profile.numeric_columns[0],
                        "agg": "mean",
                    },
                )
            if profile.datetime_columns:
                add(
                    "step_3",
                    "Assess time trend for primary numeric metric.",
                    OperationType.TREND,
                    {
                        "datetime_column": profile.datetime_columns[0],
                        "target_column": profile.numeric_columns[0] if profile.numeric_columns else None,
                    },
                )

        elif intent.intent_type == IntentType.DIAGNOSTIC:
            add("step_1", "Generate baseline summary.", OperationType.SUMMARY, {})
            if profile.categorical_columns and profile.numeric_columns:
                add(
                    "step_2",
                    "Run segment comparison by category.",
                    OperationType.GROUPBY,
                    {
                        "group_by": profile.categorical_columns[0],
                        "target_column": profile.numeric_columns[0],
                        "agg": "mean",
                    },
                )
            add("step_3", "Compute numeric correlation matrix.", OperationType.CORRELATION, {})

        elif intent.intent_type == IntentType.PREDICTIVE:
            target = intent.target_columns[0] if intent.target_columns else (
                profile.numeric_columns[-1] if profile.numeric_columns else (profile.categorical_columns[-1] if profile.categorical_columns else None)
            )
            add(
                "step_1",
                "Train baseline predictive model.",
                OperationType.TRAIN_MODEL,
                {"target_column": target},
            )
            add("step_2", "Evaluate baseline predictive model.", OperationType.EVALUATE_MODEL, {})

        elif intent.intent_type == IntentType.DATA_CLEANING:
            add(
                "step_1",
                "Apply cleaning operations for missing/duplicates/outliers.",
                OperationType.CLEAN_DATA,
                {
                    "operations": [
                        "drop_duplicates",
                        "fill_numeric_median",
                        "fill_categorical_mode",
                    ]
                },
            )
            add("step_2", "Summarize cleaned dataset.", OperationType.SUMMARY, {})

        return AnalysisPlan(intent_type=intent.intent_type, steps=steps).model_dump()
