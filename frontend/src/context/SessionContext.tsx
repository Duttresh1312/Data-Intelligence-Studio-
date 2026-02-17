import { createContext, useCallback, useContext, useState, type ReactNode } from "react"
import { setSessionPhase } from "../api/client"
import type {
  AnalysisPlan,
  ConversationMessage,
  DatasetProfile,
  DatasetSummaryReport,
  DriverInsightReport,
  DriverRanking,
  DomainClassification,
  ExecutionResult,
  HypothesisSet,
  IntentClassification,
  MissingValueSolution,
  MissingValueTreatmentResult,
  StatisticalResult,
  StudioPhase,
} from "../types"

interface SessionContextValue {
  sessionId: string | null
  currentPhase: StudioPhase
  datasetProfile: DatasetProfile | null
  domainClassification: DomainClassification | null
  datasetSummaryReport: DatasetSummaryReport | null
  intentClassification: IntentClassification | null
  analysisPlan: AnalysisPlan | null
  executionResults: ExecutionResult[]
  hypothesisSet: HypothesisSet | null
  statisticalResults: StatisticalResult[]
  driverRanking: DriverRanking | null
  driverInsightReport: DriverInsightReport | null
  missingValueSolutions: MissingValueSolution[]
  lastMissingTreatmentResult: MissingValueTreatmentResult | null
  conversationHistory: ConversationMessage[]
  errors: string[]
  setUploadState: (payload: {
    sessionId: string
    phase: StudioPhase
    datasetProfile: DatasetProfile | null
  }) => void
  setStartAnalysisState: (payload: {
    phase: StudioPhase
    domainClassification: DomainClassification | null
    datasetSummaryReport: DatasetSummaryReport | null
    missingValueSolutions: MissingValueSolution[]
    lastMissingTreatmentResult: MissingValueTreatmentResult | null
    conversationHistory: ConversationMessage[]
  }) => void
  setChatState: (payload: {
    phase: StudioPhase
    conversationHistory: ConversationMessage[]
    intentClassification: IntentClassification | null
    analysisPlan: AnalysisPlan | null
  }) => void
  setExecutionState: (payload: {
    phase: StudioPhase
    executionResults: ExecutionResult[]
    hypothesisSet?: HypothesisSet | null
    statisticalResults?: StatisticalResult[]
    driverRanking?: DriverRanking | null
    driverInsightReport?: DriverInsightReport | null
  }) => void
  setMissingTreatmentState: (payload: {
    phase: StudioPhase
    datasetProfile: DatasetProfile | null
    datasetSummaryReport: DatasetSummaryReport | null
    missingValueSolutions: MissingValueSolution[]
    lastMissingTreatmentResult: MissingValueTreatmentResult | null
  }) => void
  setPhase: (phase: StudioPhase) => void
  goBackPhase: () => Promise<void>
  setErrors: (errors: string[]) => void
  clearSession: () => void
}

const SessionContext = createContext<SessionContextValue | null>(null)

function readJSON<T>(key: string, fallback: T): T {
  const raw = sessionStorage.getItem(key)
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const phaseOrder: StudioPhase[] = [
    "LANDING",
    "DATA_UPLOADED",
    "PROFILE_READY",
    "WAITING_FOR_INTENT",
  ]
  const normalizePhase = (phase: StudioPhase): StudioPhase => {
    if (phase === "PLAN_READY" || phase === "EXECUTING" || phase === "COMPLETED") {
      return "WAITING_FOR_INTENT"
    }
    return phase
  }
  const [sessionId, setSessionId] = useState<string | null>(() => sessionStorage.getItem("studio_session_id"))
  const [currentPhase, setCurrentPhase] = useState<StudioPhase>(
    () => normalizePhase((sessionStorage.getItem("studio_current_phase") as StudioPhase) || "LANDING")
  )
  const [datasetProfile, setDatasetProfile] = useState<DatasetProfile | null>(() =>
    readJSON<DatasetProfile | null>("studio_dataset_profile", null)
  )
  const [domainClassification, setDomainClassification] = useState<DomainClassification | null>(() =>
    readJSON<DomainClassification | null>("studio_domain_classification", null)
  )
  const [datasetSummaryReport, setDatasetSummaryReport] = useState<DatasetSummaryReport | null>(() =>
    readJSON<DatasetSummaryReport | null>("studio_dataset_summary_report", null)
  )
  const [intentClassification, setIntentClassification] = useState<IntentClassification | null>(() =>
    readJSON<IntentClassification | null>("studio_intent_classification", null)
  )
  const [analysisPlan, setAnalysisPlan] = useState<AnalysisPlan | null>(() =>
    readJSON<AnalysisPlan | null>("studio_analysis_plan", null)
  )
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>(() =>
    readJSON<ConversationMessage[]>("studio_conversation_history", [])
  )
  const [executionResults, setExecutionResults] = useState<ExecutionResult[]>(() =>
    readJSON<ExecutionResult[]>("studio_execution_results", [])
  )
  const [hypothesisSet, setHypothesisSet] = useState<HypothesisSet | null>(() =>
    readJSON<HypothesisSet | null>("studio_hypothesis_set", null)
  )
  const [statisticalResults, setStatisticalResults] = useState<StatisticalResult[]>(() =>
    readJSON<StatisticalResult[]>("studio_statistical_results", [])
  )
  const [driverRanking, setDriverRanking] = useState<DriverRanking | null>(() =>
    readJSON<DriverRanking | null>("studio_driver_ranking", null)
  )
  const [driverInsightReport, setDriverInsightReport] = useState<DriverInsightReport | null>(() =>
    readJSON<DriverInsightReport | null>("studio_driver_insight_report", null)
  )
  const [missingValueSolutions, setMissingValueSolutions] = useState<MissingValueSolution[]>(() =>
    readJSON<MissingValueSolution[]>("studio_missing_value_solutions", [])
  )
  const [lastMissingTreatmentResult, setLastMissingTreatmentResult] =
    useState<MissingValueTreatmentResult | null>(() =>
      readJSON<MissingValueTreatmentResult | null>("studio_last_missing_treatment_result", null)
    )
  const [errors, setErrorsState] = useState<string[]>(() => readJSON<string[]>("studio_errors", []))

  const setPhase = useCallback((phase: StudioPhase) => {
    const normalized = normalizePhase(phase)
    setCurrentPhase(normalized)
    sessionStorage.setItem("studio_current_phase", normalized)
  }, [])

  const goBackPhase = useCallback(async () => {
    const currentIndex = phaseOrder.indexOf(currentPhase)
    if (currentIndex <= 0) return
    const previousPhase = phaseOrder[currentIndex - 1]
    if (sessionId) {
      try {
        const response = await setSessionPhase(sessionId, previousPhase)
        setCurrentPhase(response.phase)
        sessionStorage.setItem("studio_current_phase", response.phase)
      } catch {
        return
      }
      return
    }
    setCurrentPhase(previousPhase)
    sessionStorage.setItem("studio_current_phase", previousPhase)
  }, [currentPhase, sessionId])

  const setErrors = useCallback((nextErrors: string[]) => {
    setErrorsState(nextErrors)
    sessionStorage.setItem("studio_errors", JSON.stringify(nextErrors))
  }, [])

  const setUploadState = useCallback((payload: {
    sessionId: string
    phase: StudioPhase
    datasetProfile: DatasetProfile | null
  }) => {
    setSessionId(payload.sessionId)
    sessionStorage.setItem("studio_session_id", payload.sessionId)

    setPhase(payload.phase)
    setDatasetProfile(payload.datasetProfile)
    setExecutionResults([])
    setHypothesisSet(null)
    setStatisticalResults([])
    setDriverRanking(null)
    setDriverInsightReport(null)
    setMissingValueSolutions([])
    setLastMissingTreatmentResult(null)
    sessionStorage.setItem("studio_dataset_profile", JSON.stringify(payload.datasetProfile))
    sessionStorage.setItem("studio_execution_results", JSON.stringify([]))
    sessionStorage.setItem("studio_hypothesis_set", JSON.stringify(null))
    sessionStorage.setItem("studio_statistical_results", JSON.stringify([]))
    sessionStorage.setItem("studio_driver_ranking", JSON.stringify(null))
    sessionStorage.setItem("studio_driver_insight_report", JSON.stringify(null))
    sessionStorage.setItem("studio_missing_value_solutions", JSON.stringify([]))
    sessionStorage.setItem("studio_last_missing_treatment_result", JSON.stringify(null))
  }, [setPhase])

  const setStartAnalysisState = useCallback((payload: {
    phase: StudioPhase
    domainClassification: DomainClassification | null
    datasetSummaryReport: DatasetSummaryReport | null
    missingValueSolutions: MissingValueSolution[]
    lastMissingTreatmentResult: MissingValueTreatmentResult | null
    conversationHistory: ConversationMessage[]
  }) => {
    setPhase(payload.phase)
    setDomainClassification(payload.domainClassification)
    setDatasetSummaryReport(payload.datasetSummaryReport)
    setExecutionResults([])
    setHypothesisSet(null)
    setStatisticalResults([])
    setDriverRanking(null)
    setDriverInsightReport(null)
    setMissingValueSolutions(payload.missingValueSolutions)
    setLastMissingTreatmentResult(payload.lastMissingTreatmentResult)
    setConversationHistory(payload.conversationHistory)
    sessionStorage.setItem("studio_domain_classification", JSON.stringify(payload.domainClassification))
    sessionStorage.setItem("studio_dataset_summary_report", JSON.stringify(payload.datasetSummaryReport))
    sessionStorage.setItem("studio_execution_results", JSON.stringify([]))
    sessionStorage.setItem("studio_hypothesis_set", JSON.stringify(null))
    sessionStorage.setItem("studio_statistical_results", JSON.stringify([]))
    sessionStorage.setItem("studio_driver_ranking", JSON.stringify(null))
    sessionStorage.setItem("studio_driver_insight_report", JSON.stringify(null))
    sessionStorage.setItem("studio_missing_value_solutions", JSON.stringify(payload.missingValueSolutions))
    sessionStorage.setItem("studio_last_missing_treatment_result", JSON.stringify(payload.lastMissingTreatmentResult))
    sessionStorage.setItem("studio_conversation_history", JSON.stringify(payload.conversationHistory))
  }, [setPhase])

  const setChatState = useCallback((payload: {
    phase: StudioPhase
    conversationHistory: ConversationMessage[]
    intentClassification: IntentClassification | null
    analysisPlan: AnalysisPlan | null
  }) => {
    setPhase(payload.phase)
    setConversationHistory(payload.conversationHistory)
    setIntentClassification(payload.intentClassification)
    setAnalysisPlan(payload.analysisPlan)
    sessionStorage.setItem("studio_conversation_history", JSON.stringify(payload.conversationHistory))
    sessionStorage.setItem("studio_intent_classification", JSON.stringify(payload.intentClassification))
    sessionStorage.setItem("studio_analysis_plan", JSON.stringify(payload.analysisPlan))
  }, [setPhase])

  const setExecutionState = useCallback((payload: {
    phase: StudioPhase
    executionResults: ExecutionResult[]
    hypothesisSet?: HypothesisSet | null
    statisticalResults?: StatisticalResult[]
    driverRanking?: DriverRanking | null
    driverInsightReport?: DriverInsightReport | null
  }) => {
    setPhase(payload.phase)
    setExecutionResults(payload.executionResults)
    if (payload.hypothesisSet !== undefined) setHypothesisSet(payload.hypothesisSet)
    if (payload.statisticalResults !== undefined) setStatisticalResults(payload.statisticalResults)
    if (payload.driverRanking !== undefined) setDriverRanking(payload.driverRanking)
    if (payload.driverInsightReport !== undefined) setDriverInsightReport(payload.driverInsightReport)
    sessionStorage.setItem("studio_execution_results", JSON.stringify(payload.executionResults))
    if (payload.hypothesisSet !== undefined) {
      sessionStorage.setItem("studio_hypothesis_set", JSON.stringify(payload.hypothesisSet))
    }
    if (payload.statisticalResults !== undefined) {
      sessionStorage.setItem("studio_statistical_results", JSON.stringify(payload.statisticalResults))
    }
    if (payload.driverRanking !== undefined) {
      sessionStorage.setItem("studio_driver_ranking", JSON.stringify(payload.driverRanking))
    }
    if (payload.driverInsightReport !== undefined) {
      sessionStorage.setItem("studio_driver_insight_report", JSON.stringify(payload.driverInsightReport))
    }
  }, [setPhase])

  const setMissingTreatmentState = useCallback((payload: {
    phase: StudioPhase
    datasetProfile: DatasetProfile | null
    datasetSummaryReport: DatasetSummaryReport | null
    missingValueSolutions: MissingValueSolution[]
    lastMissingTreatmentResult: MissingValueTreatmentResult | null
  }) => {
    setPhase(payload.phase)
    setDatasetProfile(payload.datasetProfile)
    setDatasetSummaryReport(payload.datasetSummaryReport)
    setMissingValueSolutions(payload.missingValueSolutions)
    setLastMissingTreatmentResult(payload.lastMissingTreatmentResult)
    sessionStorage.setItem("studio_dataset_profile", JSON.stringify(payload.datasetProfile))
    sessionStorage.setItem("studio_dataset_summary_report", JSON.stringify(payload.datasetSummaryReport))
    sessionStorage.setItem("studio_missing_value_solutions", JSON.stringify(payload.missingValueSolutions))
    sessionStorage.setItem(
      "studio_last_missing_treatment_result",
      JSON.stringify(payload.lastMissingTreatmentResult)
    )
  }, [setPhase])

  const clearSession = useCallback(() => {
    setSessionId(null)
    setCurrentPhase("LANDING")
    setDatasetProfile(null)
    setDomainClassification(null)
    setDatasetSummaryReport(null)
    setIntentClassification(null)
    setAnalysisPlan(null)
    setExecutionResults([])
    setHypothesisSet(null)
    setStatisticalResults([])
    setDriverRanking(null)
    setDriverInsightReport(null)
    setMissingValueSolutions([])
    setLastMissingTreatmentResult(null)
    setConversationHistory([])
    setErrorsState([])
    const keys = [
      "studio_session_id",
      "studio_current_phase",
      "studio_dataset_profile",
      "studio_domain_classification",
      "studio_dataset_summary_report",
      "studio_intent_classification",
      "studio_analysis_plan",
      "studio_execution_results",
      "studio_hypothesis_set",
      "studio_statistical_results",
      "studio_driver_ranking",
      "studio_driver_insight_report",
      "studio_missing_value_solutions",
      "studio_last_missing_treatment_result",
      "studio_conversation_history",
      "studio_errors",
    ]
    keys.forEach((key) => sessionStorage.removeItem(key))
  }, [])

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        currentPhase,
        datasetProfile,
        domainClassification,
        datasetSummaryReport,
        intentClassification,
        analysisPlan,
        executionResults,
        hypothesisSet,
        statisticalResults,
        driverRanking,
        driverInsightReport,
        missingValueSolutions,
        lastMissingTreatmentResult,
        conversationHistory,
        errors,
        setUploadState,
        setStartAnalysisState,
        setChatState,
        setExecutionState,
        setMissingTreatmentState,
        setPhase,
        goBackPhase,
        setErrors,
        clearSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) throw new Error("useSession must be used within SessionProvider")
  return context
}
