export type StudioPhase =
  | "LANDING"
  | "DATA_UPLOADED"
  | "PROFILE_READY"
  | "WAITING_FOR_INTENT"
  | "PLAN_READY"
  | "EXECUTING"
  | "COMPLETED"

export interface ConversationMessage {
  role: "system" | "assistant" | "user"
  content: string
  timestamp: string
}

export interface DatasetProfile {
  total_rows: number
  total_columns: number
  numeric_columns: string[]
  categorical_columns: string[]
  datetime_columns: string[]
  missing_percentage: Record<string, number>
  duplicate_rows: number
  potential_primary_keys: string[]
  column_roles: Record<string, ColumnRole>
  column_summary: Record<string, Record<string, string | number | null>>
}

export type ColumnRole =
  | "IDENTIFIER"
  | "NUMERIC_METRIC"
  | "CATEGORICAL_DIMENSION"
  | "DATETIME"
  | "BOOLEAN"
  | "TEXT"

export interface DomainClassification {
  domain_label: string
  confidence: number
  reasoning: string
  suggested_kpis: string[]
}

export interface DatasetSummaryReport {
  executive_summary: string
  data_health_assessment: string
  statistical_highlights: string[]
  anomaly_indicators: string[]
  recommended_starting_points: string[]
  important_features: string[]
  useful_statistics: string[]
  confidence: number
}

export interface MissingValueSolution {
  solution_id: string
  title: string
  description: string
  action_type: string
  target_columns: string[]
}

export interface MissingValueTreatmentResult {
  solution_id: string
  applied: boolean
  rows_before: number
  rows_after: number
  missing_before: number
  missing_after: number
  affected_columns: string[]
  summary: string
}

export type IntentType = "DESCRIPTIVE" | "DIAGNOSTIC" | "PREDICTIVE" | "DATA_CLEANING"

export type OperationType =
  | "SUMMARY"
  | "GROUPBY"
  | "CORRELATION"
  | "TREND"
  | "TRAIN_MODEL"
  | "EVALUATE_MODEL"
  | "CLEAN_DATA"

export interface IntentClassification {
  intent_type: IntentType
  target_columns: string[]
  explanation: string
  confidence: number
}

export interface PlanStep {
  step_id: string
  description: string
  operation_type: OperationType
  parameters: Record<string, unknown>
}

export interface AnalysisPlan {
  intent_type: IntentType
  steps: PlanStep[]
}

export interface ExecutionResult {
  step_id: string
  status: string
  result_summary: string
  metrics?: Record<string, unknown> | null
}

export interface Hypothesis {
  statement: string
  predictor_column: string
  target_column?: string | null
}

export interface HypothesisSet {
  hypotheses: Hypothesis[]
}

export interface StatisticalResult {
  predictor: string
  target?: string | null
  test_type: string
  score: number
  p_value?: number | null
  effect_size?: number | null
  feature_importance?: number | null
}

export interface DriverRanking {
  ranked_drivers: StatisticalResult[]
}

export interface DriverInsightReport {
  executive_driver_summary: string
  top_3_drivers: string[]
  strength_assessment: string
  recommended_next_step: string
  confidence: number
}

export interface UploadResponse {
  session_id: string
  phase: StudioPhase
  dataset_profile?: DatasetProfile | null
}

export interface StartAnalysisResponse {
  session_id: string
  phase: StudioPhase
  domain_classification?: DomainClassification | null
  dataset_summary_report?: DatasetSummaryReport | null
  missing_value_solutions: MissingValueSolution[]
  last_missing_treatment_result?: MissingValueTreatmentResult | null
  conversation_history: ConversationMessage[]
}

export interface ChatResponse {
  session_id: string
  phase: StudioPhase
  conversation_history: ConversationMessage[]
  intent_classification?: IntentClassification | null
  analysis_plan?: AnalysisPlan | null
}

export interface ApprovePlanResponse {
  session_id: string
  phase: StudioPhase
}

export interface SetPhaseResponse {
  session_id: string
  phase: StudioPhase
}

export interface ApplyMissingValueSolutionResponse {
  session_id: string
  phase: StudioPhase
  dataset_profile?: DatasetProfile | null
  dataset_summary_report?: DatasetSummaryReport | null
  missing_value_solutions: MissingValueSolution[]
  last_missing_treatment_result?: MissingValueTreatmentResult | null
}

export type ExecutionEventType =
  | "step_started"
  | "step_completed"
  | "step_failed"
  | "analysis_completed"
  | "heartbeat"

export interface ExecutionStreamEvent {
  type: ExecutionEventType
  payload: Record<string, unknown>
}

export interface StateResponse {
  session_id: string
  phase: StudioPhase
  file_name?: string | null
  shape?: [number, number] | null
  columns?: string[] | null
  file_size_mb?: number | null
  dataset_profile?: DatasetProfile | null
  domain_classification?: DomainClassification | null
  dataset_summary_report?: DatasetSummaryReport | null
  intent_classification?: IntentClassification | null
  analysis_plan?: AnalysisPlan | null
  execution_results: ExecutionResult[]
  hypothesis_set?: HypothesisSet | null
  statistical_results: StatisticalResult[]
  driver_ranking?: DriverRanking | null
  driver_insight_report?: DriverInsightReport | null
  missing_value_solutions: MissingValueSolution[]
  last_missing_treatment_result?: MissingValueTreatmentResult | null
  conversation_history: ConversationMessage[]
  errors: string[]
}

export interface ApiError {
  detail?: string | { msg?: string }[]
}
