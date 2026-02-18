"""API request/response schemas."""

from typing import Optional

from pydantic import BaseModel

from backend.core.state import (
    AnalysisPlan,
    ConversationMessage,
    DatasetProfile,
    DatasetSummaryReport,
    DriverScore,
    DriverInsightReport,
    DriverRanking,
    DomainClassification,
    ExecutionResult,
    FinalAnalysisAnswer,
    Hypothesis,
    HypothesisSet,
    IntentClassification,
    MissingValueSolution,
    MissingValueTreatmentResult,
    ParsedIntent,
    StatisticalResultBundle,
    StatisticalResult,
    StudioPhase,
)


class UploadResponse(BaseModel):
    session_id: str
    phase: StudioPhase
    dataset_profile: DatasetProfile | None = None


class StartAnalysisRequest(BaseModel):
    session_id: str


class StartAnalysisResponse(BaseModel):
    session_id: str
    phase: StudioPhase
    domain_classification: DomainClassification | None = None
    dataset_summary_report: DatasetSummaryReport | None = None
    missing_value_solutions: list[MissingValueSolution]
    last_missing_treatment_result: MissingValueTreatmentResult | None = None
    conversation_history: list[ConversationMessage]


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    phase: StudioPhase
    conversation_history: list[ConversationMessage]
    parsed_intent: ParsedIntent | None = None
    target_column: str | None = None
    target_type: str | None = None
    generated_hypotheses: list[Hypothesis] | None = None
    statistical_results: StatisticalResultBundle | None = None
    ranked_drivers: list[DriverScore] | None = None
    final_answer: FinalAnalysisAnswer | None = None
    intent_classification: IntentClassification | None = None
    analysis_plan: AnalysisPlan | None = None


class ConfirmTargetRequest(BaseModel):
    session_id: str
    target_column: str


class ConfirmTargetResponse(BaseModel):
    session_id: str
    phase: StudioPhase
    conversation_history: list[ConversationMessage]
    parsed_intent: ParsedIntent | None = None
    target_column: str | None = None
    target_type: str | None = None
    generated_hypotheses: list[Hypothesis] | None = None
    statistical_results: StatisticalResultBundle | None = None
    ranked_drivers: list[DriverScore] | None = None
    final_answer: FinalAnalysisAnswer | None = None


class ApprovePlanRequest(BaseModel):
    session_id: str


class ApprovePlanResponse(BaseModel):
    session_id: str
    phase: StudioPhase


class SetPhaseRequest(BaseModel):
    session_id: str
    phase: StudioPhase


class SetPhaseResponse(BaseModel):
    session_id: str
    phase: StudioPhase


class ApplyMissingValueSolutionRequest(BaseModel):
    session_id: str
    solution_id: str


class ApplyMissingValueSolutionResponse(BaseModel):
    session_id: str
    phase: StudioPhase
    dataset_profile: DatasetProfile | None = None
    dataset_summary_report: DatasetSummaryReport | None = None
    missing_value_solutions: list[MissingValueSolution]
    last_missing_treatment_result: MissingValueTreatmentResult | None = None


class StateResponse(BaseModel):
    session_id: str
    phase: StudioPhase
    file_name: str | None = None
    shape: tuple[int, int] | None = None
    columns: list[str] | None = None
    file_size_mb: float | None = None
    dataset_profile: DatasetProfile | None = None
    domain_classification: DomainClassification | None = None
    dataset_summary_report: DatasetSummaryReport | None = None
    intent_classification: IntentClassification | None = None
    analysis_plan: AnalysisPlan | None = None
    execution_results: list[ExecutionResult]
    hypothesis_set: HypothesisSet | None = None
    parsed_intent: ParsedIntent | None = None
    target_column: str | None = None
    target_type: str | None = None
    generated_hypotheses: list[Hypothesis] | None = None
    statistical_results: StatisticalResultBundle | None = None
    ranked_drivers: list[DriverScore] | None = None
    final_answer: FinalAnalysisAnswer | None = None
    legacy_statistical_results: list[StatisticalResult] = []
    driver_ranking: DriverRanking | None = None
    driver_insight_report: DriverInsightReport | None = None
    missing_value_solutions: list[MissingValueSolution]
    last_missing_treatment_result: MissingValueTreatmentResult | None = None
    conversation_history: list[ConversationMessage]
    errors: list[str]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
