"""Prompt builders for structured LLM reasoning."""

from __future__ import annotations

import json

from backend.core.state import DatasetProfile, DomainClassification, IntentClassification


def build_domain_inference_system_prompt() -> str:
    return (
        "You are a data strategy analyst. "
        "Infer domain context from structured metadata and detected column roles. "
        "Avoid generic labels unless the profile has no concrete signals. "
        "Reference role distribution, metric/dimension mix, and datetime coverage. "
        "Never invent values or generate code. Return structured output only."
    )


def build_domain_inference_user_prompt(profile: DatasetProfile, column_names: list[str]) -> str:
    roles = profile.column_roles
    payload = {
        "dataset_shape": {
            "total_rows": profile.total_rows,
            "total_columns": profile.total_columns,
        },
        "column_names": column_names,
        "column_roles": {name: role.value for name, role in roles.items()},
        "metric_columns": [name for name, role in roles.items() if role.value == "NUMERIC_METRIC"],
        "dimension_columns": [name for name, role in roles.items() if role.value == "CATEGORICAL_DIMENSION"],
        "identifier_columns": [name for name, role in roles.items() if role.value == "IDENTIFIER"],
        "datetime_columns": profile.datetime_columns,
        "high_missing_columns": [name for name, pct in profile.missing_percentage.items() if pct > 10],
        "duplicate_rows": profile.duplicate_rows,
    }
    return (
        "Infer domain classification using this dataset metadata JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def build_dataset_summary_system_prompt() -> str:
    return (
        "You are a senior data analyst reviewing a dataset profile. "
        "You must infer business meaning from column roles. "
        "Avoid generic language and reference specific signals such as high missing percentages and metric ranges. "
        "If context is insufficient to determine domain, explicitly say so. "
        "Do not output 'generic tabular dataset' unless absolutely no signals exist. "
        "Highlight analytical opportunities tied to detected metric columns. "
        "If identifier columns dominate, state that this may be a lookup/reference table. "
        "If datetime exists, mention time-series potential. "
        "When analysis_guidance_enabled is true, populate important_features and useful_statistics with concrete column-linked guidance. "
        "When analysis_guidance_enabled is false, keep important_features and useful_statistics empty arrays. "
        "Do not invent values, do not infer hidden rows, and do not generate code. "
        "Return JSON only."
    )


def build_dataset_summary_user_prompt(
    llm_context: dict,
    domain_payload: dict,
    analysis_guidance_enabled: bool,
) -> str:
    payload = {
        "dataset_context": llm_context,
        "domain_classification": domain_payload,
        "analysis_guidance_enabled": analysis_guidance_enabled,
    }
    return (
        "Generate DatasetSummaryReport from this metadata JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def build_initial_insight_system_prompt() -> str:
    return build_dataset_summary_system_prompt()


def build_initial_insight_user_prompt(
    profile: DatasetProfile,
    domain_payload: dict,
) -> str:
    return build_dataset_summary_user_prompt(profile.model_dump(), domain_payload, False)


def build_intent_parser_system_prompt() -> str:
    return (
        "You classify analytics intent into a strict enum and identify plausible target columns. "
        "Use only provided metadata; never invent columns; return structured output only."
    )


def build_intent_parser_user_prompt(
    user_intent: str,
    domain: DomainClassification,
    profile: DatasetProfile,
) -> str:
    payload = {
        "user_intent": user_intent,
        "domain_classification": domain.model_dump(),
        "dataset_profile": profile.model_dump(),
    }
    return (
        "Classify intent and identify target columns from this JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def build_planner_system_prompt() -> str:
    return (
        "You build deterministic data-analysis plans using only allowed operation types. "
        "Allowed operations: SUMMARY, GROUPBY, CORRELATION, TREND, TRAIN_MODEL, EVALUATE_MODEL, CLEAN_DATA. "
        "Return structured output only."
    )


def build_planner_user_prompt(
    intent: IntentClassification,
    profile: DatasetProfile,
) -> str:
    payload = {
        "intent_classification": intent.model_dump(),
        "dataset_profile": profile.model_dump(),
    }
    return (
        "Generate an analysis plan JSON from this input:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def build_hypothesis_system_prompt() -> str:
    return (
        "You generate testable analytical hypotheses from structured metadata. "
        "Each hypothesis must map to a real predictor column and optional target column. "
        "Avoid generic statements and avoid columns not present in metadata. "
        "Return JSON only."
    )


def build_hypothesis_user_prompt(
    intent: IntentClassification,
    profile: DatasetProfile,
) -> str:
    payload = {
        "intent_classification": intent.model_dump(),
        "column_roles": {name: role.value for name, role in profile.column_roles.items()},
        "numeric_columns": profile.numeric_columns,
        "categorical_columns": profile.categorical_columns,
        "datetime_columns": profile.datetime_columns,
    }
    return (
        "Generate a HypothesisSet from this JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def build_driver_insight_system_prompt() -> str:
    return (
        "You are an analytics lead summarizing ranked statistical drivers for stakeholders. "
        "Use only provided numeric results; do not invent metrics. "
        "Reference predictor names and their relative strengths clearly. "
        "Return JSON only."
    )


def build_driver_insight_user_prompt(payload: dict) -> str:
    return (
        "Generate a DriverInsightReport from this JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def build_phase6_intent_parser_system_prompt() -> str:
    return (
        "You classify investigation intent for an AI analytics system. "
        "Output strictly valid JSON matching ParsedIntent. "
        "Use only provided metadata and user message. "
        "Do not invent columns, code, or statistics."
    )


def build_phase6_intent_parser_user_prompt(user_message: str, profile: DatasetProfile) -> str:
    payload = {
        "user_message": user_message,
        "dataset_profile": profile.model_dump(),
        "column_roles": {name: role.value for name, role in profile.column_roles.items()},
    }
    return (
        "Classify the intent and target candidates from this JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def build_phase6_insight_synthesis_system_prompt() -> str:
    return (
        "You are a senior analytics lead. "
        "Generate an evidence-based answer using only supplied statistical outputs. "
        "Must reference at least one numeric statistic. "
        "Must mention the strongest driver. "
        "If signal is weak, explicitly state uncertainty. "
        "No generic language. Return JSON only."
    )


def build_phase6_insight_synthesis_user_prompt(payload: dict) -> str:
    return (
        "Generate FinalAnalysisAnswer from this JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )
