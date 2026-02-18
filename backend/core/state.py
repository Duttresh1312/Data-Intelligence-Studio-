from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field


class StudioPhase(str, Enum):
    LANDING = "LANDING"
    DATA_UPLOADED = "DATA_UPLOADED"
    PROFILE_READY = "PROFILE_READY"
    WAITING_FOR_INTENT = "WAITING_FOR_INTENT"
    INTENT_PARSED = "INTENT_PARSED"
    TARGET_VALIDATION_REQUIRED = "TARGET_VALIDATION_REQUIRED"
    INVESTIGATING = "INVESTIGATING"
    DRIVER_RANKED = "DRIVER_RANKED"
    ANSWER_READY = "ANSWER_READY"
    PLAN_READY = "PLAN_READY"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"


class ConversationMessage(BaseModel):
    role: Literal["system", "assistant", "user"]
    content: str
    timestamp: datetime


class DatasetProfile(BaseModel):
    total_rows: int
    total_columns: int
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    missing_percentage: Dict[str, float]
    duplicate_rows: int
    potential_primary_keys: List[str]
    column_roles: Dict[str, "ColumnRole"]
    column_summary: Dict[str, Dict[str, Any]]


class ColumnRole(str, Enum):
    IDENTIFIER = "IDENTIFIER"
    NUMERIC_METRIC = "NUMERIC_METRIC"
    CATEGORICAL_DIMENSION = "CATEGORICAL_DIMENSION"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"


class DomainClassification(BaseModel):
    domain_label: str
    confidence: float
    reasoning: str
    suggested_kpis: List[str]


class DatasetSummaryReport(BaseModel):
    executive_summary: str
    data_health_assessment: str
    statistical_highlights: List[str]
    anomaly_indicators: List[str]
    important_features: List[str]
    useful_statistics: List[str]
    confidence: float


class MissingValueSolution(BaseModel):
    solution_id: str
    title: str
    description: str
    action_type: str
    target_columns: List[str] = Field(default_factory=list)


class MissingValueTreatmentResult(BaseModel):
    solution_id: str
    applied: bool
    rows_before: int
    rows_after: int
    missing_before: int
    missing_after: int
    affected_columns: List[str] = Field(default_factory=list)
    summary: str


class IntentType(str, Enum):
    DESCRIPTIVE = "DESCRIPTIVE"
    DIAGNOSTIC = "DIAGNOSTIC"
    PREDICTIVE = "PREDICTIVE"
    EXPLANATORY = "EXPLANATORY"
    DATA_CLEANING = "DATA_CLEANING"


class OperationType(str, Enum):
    SUMMARY = "SUMMARY"
    GROUPBY = "GROUPBY"
    CORRELATION = "CORRELATION"
    TREND = "TREND"
    TRAIN_MODEL = "TRAIN_MODEL"
    EVALUATE_MODEL = "EVALUATE_MODEL"
    CLEAN_DATA = "CLEAN_DATA"


class IntentClassification(BaseModel):
    intent_type: IntentType
    target_columns: List[str]
    explanation: str
    confidence: float


class PlanStep(BaseModel):
    step_id: str
    description: str
    operation_type: OperationType
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AnalysisPlan(BaseModel):
    intent_type: IntentType
    steps: List[PlanStep]


class ExecutionResult(BaseModel):
    step_id: str
    status: str
    result_summary: str
    metrics: Optional[Dict[str, Any]] = None


class Hypothesis(BaseModel):
    feature: str
    type: Literal["correlation", "group_difference", "classification_signal"]
    description: str


class HypothesisSet(BaseModel):
    hypotheses: List[Hypothesis] = Field(default_factory=list)


class StatisticalFeatureResult(BaseModel):
    feature: str
    test_type: str
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    correlation: Optional[float] = None
    feature_importance: Optional[float] = None
    confidence_score: float = 0.0


class StatisticalResultBundle(BaseModel):
    target_column: str
    target_type: Literal["classification", "regression"]
    model_type_used: str
    data_quality_flags: List[str] = Field(default_factory=list)
    results: List[StatisticalFeatureResult] = Field(default_factory=list)


class StatisticalResult(BaseModel):
    predictor: str
    target: Optional[str] = None
    test_type: str
    score: float
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    feature_importance: Optional[float] = None


class DriverScore(BaseModel):
    feature: str
    strength_score: float
    importance_rank: int
    statistical_significance: str
    explanation_hint: str
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    feature_importance: Optional[float] = None
    correlation: Optional[float] = None


class ParsedIntent(BaseModel):
    intent_type: Literal["DESCRIPTIVE", "DIAGNOSTIC", "PREDICTIVE", "EXPLANATORY"]
    target_candidates: List[str] = Field(default_factory=list)
    requires_target: bool = True
    reasoning: str


class FinalAnalysisAnswer(BaseModel):
    direct_answer: str
    key_drivers_summary: str
    evidence_points: List[str] = Field(default_factory=list)
    business_impact: str
    confidence_score: float
    recommended_next_step: str


class DriverRanking(BaseModel):
    ranked_drivers: List[StatisticalResult] = Field(default_factory=list)


class DriverInsightReport(BaseModel):
    executive_driver_summary: str
    top_3_drivers: List[str]
    strength_assessment: str
    recommended_next_step: str
    confidence: float


class StudioState(BaseModel):
    raw_file_name: Optional[str] = None
    dataframe_shape: Optional[Tuple[int, int]] = None
    dataframe_columns: Optional[List[str]] = None
    file_size_mb: Optional[float] = None
    dataframe: Optional[pd.DataFrame] = None

    dataset_profile: Optional[DatasetProfile] = None
    domain_classification: Optional[DomainClassification] = None
    dataset_summary_report: Optional[DatasetSummaryReport] = None
    missing_value_solutions: List[MissingValueSolution] = Field(default_factory=list)
    last_missing_treatment_result: Optional[MissingValueTreatmentResult] = None

    user_intent: Optional[str] = None
    parsed_intent: Optional[ParsedIntent] = None
    target_column: Optional[str] = None
    target_type: Optional[Literal["classification", "regression"]] = None
    generated_hypotheses: Optional[List[Hypothesis]] = None
    statistical_results: Optional[StatisticalResultBundle] = None
    ranked_drivers: Optional[List[DriverScore]] = None
    final_answer: Optional[FinalAnalysisAnswer] = None
    intent_classification: Optional[IntentClassification] = None
    analysis_plan: Optional[AnalysisPlan] = None
    execution_results: List[ExecutionResult] = Field(default_factory=list)
    hypothesis_set: Optional[HypothesisSet] = None
    driver_ranking: Optional[DriverRanking] = None
    driver_insight_report: Optional[DriverInsightReport] = None

    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    current_phase: StudioPhase = StudioPhase.LANDING
    errors: List[str] = Field(default_factory=list)

    model_config = {
        "arbitrary_types_allowed": True,
    }
