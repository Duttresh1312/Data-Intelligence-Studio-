"""FastAPI routes for progressive phase-driven flow."""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from backend.api.schemas import (
    ApplyMissingValueSolutionRequest,
    ApplyMissingValueSolutionResponse,
    ApprovePlanRequest,
    ApprovePlanResponse,
    ChatRequest,
    ChatResponse,
    ConfirmTargetRequest,
    ConfirmTargetResponse,
    SetPhaseRequest,
    SetPhaseResponse,
    StartAnalysisRequest,
    StartAnalysisResponse,
    StateResponse,
    UploadResponse,
)
from backend.agents.driver_ranking import DriverRankingEngine
from backend.agents.hypothesis_generator import HypothesisGeneratorAgent
from backend.agents.insight_synthesis import InsightSynthesisAgent
from backend.agents.intent_parser import IntentParserAgent
from backend.agents.execution_engine import ExecutionEngineAgent
from backend.agents.missing_value_treatment import MissingValueTreatmentAgent
from backend.agents.profiling import ProfilingAgent
from backend.agents.dataset_summary import DatasetSummaryAgent
from backend.agents.statistical_engine import StatisticalTestEngine
from backend.config import settings
from backend.core.graph import StudioGraph
from backend.core.state import ConversationMessage, ParsedIntent, StudioPhase, StudioState

router = APIRouter()
state_store: dict[str, StudioState] = {}
active_connections: dict[str, WebSocket] = {}


def _infer_target_type(state: StudioState, target_column: str) -> str:
    if state.dataframe is None or target_column not in state.dataframe.columns:
        return "classification"
    series = state.dataframe[target_column].dropna()
    if series.empty:
        return "classification"
    if series.dtype.kind in {"i", "u", "f"} and series.nunique() > 10:
        return "regression"
    return "classification"


def _suggest_target_candidates(state: StudioState) -> list[str]:
    profile = state.dataset_profile
    df = state.dataframe
    if profile is None or df is None:
        return []

    candidates: list[str] = []
    class_keywords = ("status", "approved", "default", "churn", "label", "outcome")
    reg_keywords = ("revenue", "income", "score", "amount", "risk")

    for column in df.columns:
        series = df[column].dropna()
        if series.empty:
            continue
        col_l = column.lower()
        if any(key in col_l for key in class_keywords + reg_keywords):
            candidates.append(column)
            continue
        if series.dtype.kind not in {"i", "u", "f"}:
            if 2 <= series.nunique() <= 6:
                candidates.append(column)
            continue
        if series.nunique() <= 10:
            candidates.append(column)
            continue
        std = float(series.std()) if series.shape[0] > 1 else 0.0
        if std > 0 and series.nunique() >= max(20, int(0.05 * len(series))):
            candidates.append(column)

    return list(dict.fromkeys(candidates))[:8]


def _resolve_targets(state: StudioState, parsed_intent: ParsedIntent) -> list[str]:
    available = set(state.dataframe_columns or [])
    explicit = [col for col in parsed_intent.target_candidates if col in available]
    if explicit:
        return explicit
    return _suggest_target_candidates(state)


async def _run_goal_driven_investigation(
    state: StudioState,
    user_question: str,
    selected_target: str,
) -> StudioState:
    if state.dataframe is None or state.dataset_profile is None:
        raise HTTPException(status_code=400, detail="Dataset context unavailable for investigation.")

    state.target_column = selected_target
    state.target_type = _infer_target_type(state, selected_target)  # classification | regression
    state.current_phase = StudioPhase.INVESTIGATING

    hypothesis_agent = HypothesisGeneratorAgent()
    state.generated_hypotheses = hypothesis_agent.generate(
        dataset_profile=state.dataset_profile,
        target_column=selected_target,
        target_type=state.target_type,
    )

    stats_engine = StatisticalTestEngine()
    state.statistical_results = stats_engine.run(
        dataframe=state.dataframe,
        hypotheses=state.generated_hypotheses or [],
        target_column=selected_target,
        target_type=state.target_type,
    )

    ranking_engine = DriverRankingEngine()
    state.ranked_drivers = ranking_engine.rank(state.statistical_results)
    state.current_phase = StudioPhase.DRIVER_RANKED

    synthesis_agent = InsightSynthesisAgent()
    state.final_answer = await synthesis_agent.synthesize(
        user_question=user_question,
        target_column=selected_target,
        target_type=state.target_type,
        ranked_drivers=state.ranked_drivers or [],
        statistical_summary=state.statistical_results,
    )

    state.conversation_history.append(
        ConversationMessage(
            role="assistant",
            content=state.final_answer.direct_answer,
            timestamp=datetime.now(timezone.utc),
        )
    )
    state.current_phase = StudioPhase.ANSWER_READY
    return state


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile):
    """Phase 1/2 only: ingestion + profiling."""
    graph = StudioGraph()
    state = await graph.run_upload_pipeline(file)
    session_id = str(uuid4())
    state_store[session_id] = state
    return UploadResponse(
        session_id=session_id,
        phase=state.current_phase,
        dataset_profile=state.dataset_profile,
    )


@router.post("/start-analysis", response_model=StartAnalysisResponse)
async def start_analysis(request: StartAnalysisRequest):
    """Trigger domain inference + dataset intelligence summary after profile is ready."""
    state = state_store.get(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if state.current_phase != StudioPhase.PROFILE_READY:
        raise HTTPException(status_code=400, detail=f"Cannot start analysis at phase: {state.current_phase.value}")

    graph = StudioGraph()
    graph.state = state
    state = await graph.run_start_analysis()
    state_store[request.session_id] = state

    return StartAnalysisResponse(
        session_id=request.session_id,
        phase=state.current_phase,
        domain_classification=state.domain_classification,
        dataset_summary_report=state.dataset_summary_report,
        missing_value_solutions=state.missing_value_solutions,
        last_missing_treatment_result=state.last_missing_treatment_result,
        conversation_history=state.conversation_history,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Goal-driven investigation orchestration from WAITING_FOR_INTENT."""
    state = state_store.get(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if state.dataset_profile is None:
        raise HTTPException(status_code=400, detail="Dataset profile not found for this session.")

    state.user_intent = request.message
    state.conversation_history.append(
        ConversationMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now(timezone.utc),
        )
    )

    if state.current_phase in {StudioPhase.WAITING_FOR_INTENT, StudioPhase.ANSWER_READY}:
        parser = IntentParserAgent()
        state.parsed_intent = await parser.parse(request.message, state.dataset_profile)
        state.current_phase = StudioPhase.INTENT_PARSED

        candidates = _resolve_targets(state, state.parsed_intent)
        if not candidates:
            state.current_phase = StudioPhase.TARGET_VALIDATION_REQUIRED
            state.conversation_history.append(
                ConversationMessage(
                    role="assistant",
                    content="I could not infer a reliable outcome column. Please select the target column to analyze.",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        elif len(candidates) > 1:
            state.current_phase = StudioPhase.TARGET_VALIDATION_REQUIRED
            state.parsed_intent.target_candidates = candidates
            state.conversation_history.append(
                ConversationMessage(
                    role="assistant",
                    content=(
                        "I detected multiple possible outcome columns: "
                        f"{', '.join(candidates[:6])}. Which one should I analyze?"
                    ),
                    timestamp=datetime.now(timezone.utc),
                )
            )
        else:
            state = await _run_goal_driven_investigation(
                state=state,
                user_question=request.message,
                selected_target=candidates[0],
            )
    elif state.current_phase == StudioPhase.TARGET_VALIDATION_REQUIRED:
        state.conversation_history.append(
            ConversationMessage(
                role="assistant",
                content="Please confirm the target from the dropdown before I continue the investigation.",
                timestamp=datetime.now(timezone.utc),
            )
        )
    else:
        state.conversation_history.append(
            ConversationMessage(
                role="assistant",
                content=f"Current phase is {state.current_phase.value}. Submit a goal when phase is WAITING_FOR_INTENT.",
                timestamp=datetime.now(timezone.utc),
            )
        )

    state_store[request.session_id] = state
    return ChatResponse(
        session_id=request.session_id,
        phase=state.current_phase,
        conversation_history=state.conversation_history,
        parsed_intent=state.parsed_intent,
        target_column=state.target_column,
        target_type=state.target_type,
        generated_hypotheses=state.generated_hypotheses,
        statistical_results=state.statistical_results,
        ranked_drivers=state.ranked_drivers,
        final_answer=state.final_answer,
        intent_classification=state.intent_classification,
        analysis_plan=state.analysis_plan,
    )


@router.post("/confirm-target", response_model=ConfirmTargetResponse)
async def confirm_target(request: ConfirmTargetRequest):
    state = state_store.get(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if state.current_phase != StudioPhase.TARGET_VALIDATION_REQUIRED:
        raise HTTPException(status_code=400, detail=f"Target confirmation not allowed at phase: {state.current_phase.value}")
    if state.dataframe is None or request.target_column not in state.dataframe.columns:
        raise HTTPException(status_code=400, detail="Selected target column is not valid for this dataset.")

    user_question = state.user_intent or "Investigate key drivers for the selected target."
    state.conversation_history.append(
        ConversationMessage(
            role="user",
            content=f"Target confirmed: {request.target_column}",
            timestamp=datetime.now(timezone.utc),
        )
    )
    state = await _run_goal_driven_investigation(
        state=state,
        user_question=user_question,
        selected_target=request.target_column,
    )
    state_store[request.session_id] = state
    return ConfirmTargetResponse(
        session_id=request.session_id,
        phase=state.current_phase,
        conversation_history=state.conversation_history,
        parsed_intent=state.parsed_intent,
        target_column=state.target_column,
        target_type=state.target_type,
        generated_hypotheses=state.generated_hypotheses,
        statistical_results=state.statistical_results,
        ranked_drivers=state.ranked_drivers,
        final_answer=state.final_answer,
    )


async def _run_execution_task(session_id: str) -> None:
    state = state_store.get(session_id)
    if state is None or state.analysis_plan is None:
        return
    engine = ExecutionEngineAgent()
    websocket = None
    for _ in range(10):
        websocket = active_connections.get(session_id)
        if websocket is not None:
            break
        await asyncio.sleep(0.2)
    try:
        await engine.execute_plan(state.analysis_plan, state, websocket)
        if state.driver_insight_report is not None:
            state.conversation_history.append(
                ConversationMessage(
                    role="assistant",
                    content=state.driver_insight_report.executive_driver_summary,
                    timestamp=datetime.now(timezone.utc),
                )
            )
    except Exception as exc:
        state.errors.append(str(exc))
        state.current_phase = StudioPhase.COMPLETED
        if websocket is not None:
            await websocket.send_json(
                {
                    "type": "step_failed",
                    "payload": {"step_id": "execution", "error": str(exc)},
                }
            )
            await websocket.send_json(
                {
                    "type": "analysis_completed",
                    "payload": {
                        "phase": state.current_phase.value,
                        "execution_results": [result.model_dump() for result in state.execution_results],
                    },
                }
            )


@router.post("/approve-plan", response_model=ApprovePlanResponse)
async def approve_plan(request: ApprovePlanRequest):
    state = state_store.get(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if state.current_phase != StudioPhase.PLAN_READY:
        raise HTTPException(status_code=400, detail=f"Cannot approve at phase: {state.current_phase.value}")
    if state.analysis_plan is None:
        raise HTTPException(status_code=400, detail="Analysis plan is not available")
    if state.dataframe is None:
        raise HTTPException(status_code=400, detail="Dataframe is not available for execution")

    state.current_phase = StudioPhase.EXECUTING
    state.execution_results = []
    state.hypothesis_set = None
    state.generated_hypotheses = None
    state.statistical_results = None
    state.ranked_drivers = None
    state.final_answer = None
    state.driver_ranking = None
    state.driver_insight_report = None
    state_store[request.session_id] = state
    asyncio.create_task(_run_execution_task(request.session_id))
    return ApprovePlanResponse(session_id=request.session_id, phase=state.current_phase)


@router.post("/set-phase", response_model=SetPhaseResponse)
async def set_phase(request: SetPhaseRequest):
    state = state_store.get(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    phase_order = [
        StudioPhase.LANDING,
        StudioPhase.DATA_UPLOADED,
        StudioPhase.PROFILE_READY,
        StudioPhase.WAITING_FOR_INTENT,
        StudioPhase.INTENT_PARSED,
        StudioPhase.TARGET_VALIDATION_REQUIRED,
        StudioPhase.INVESTIGATING,
        StudioPhase.DRIVER_RANKED,
        StudioPhase.ANSWER_READY,
        StudioPhase.PLAN_READY,
        StudioPhase.EXECUTING,
        StudioPhase.COMPLETED,
    ]
    current_index = phase_order.index(state.current_phase)
    target_index = phase_order.index(request.phase)
    if target_index > current_index:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move phase forward via set-phase: {state.current_phase.value} -> {request.phase.value}",
        )

    state.current_phase = request.phase
    if target_index < phase_order.index(StudioPhase.EXECUTING):
        state.execution_results = []
        state.hypothesis_set = None
        state.generated_hypotheses = None
        state.statistical_results = None
        state.ranked_drivers = None
        state.final_answer = None
        state.driver_ranking = None
        state.driver_insight_report = None
    state_store[request.session_id] = state
    return SetPhaseResponse(session_id=request.session_id, phase=state.current_phase)


@router.post("/apply-missing-solution", response_model=ApplyMissingValueSolutionResponse)
async def apply_missing_solution(request: ApplyMissingValueSolutionRequest):
    state = state_store.get(request.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if state.current_phase != StudioPhase.WAITING_FOR_INTENT:
        raise HTTPException(status_code=400, detail=f"Missing treatment allowed at WAITING_FOR_INTENT only.")
    if state.dataframe is None or state.dataset_profile is None:
        raise HTTPException(status_code=400, detail="Dataset is not available for missing-value treatment.")

    solution = next(
        (item for item in state.missing_value_solutions if item.solution_id == request.solution_id),
        None,
    )
    if solution is None:
        raise HTTPException(status_code=404, detail="Missing-value solution not found.")

    missing_agent = MissingValueTreatmentAgent()
    dataframe_after, treatment_result = missing_agent.apply(
        dataframe=state.dataframe,
        profile=state.dataset_profile,
        solution=solution,
    )
    state.dataframe = dataframe_after
    state.last_missing_treatment_result = treatment_result

    profiler = ProfilingAgent()
    state.dataset_profile = profiler.profile(state.dataframe)
    state.missing_value_solutions = missing_agent.suggest(state.dataset_profile)

    if state.domain_classification is not None:
        overall_missing = int(state.dataframe.isna().sum().sum())
        guidance_enabled = overall_missing == 0
        summary_agent = DatasetSummaryAgent()
        state.dataset_summary_report = await summary_agent.generate(
            profile=state.dataset_profile,
            domain_classification=state.domain_classification,
            include_analysis_guidance=guidance_enabled,
        )
    state.conversation_history.append(
        ConversationMessage(
            role="assistant",
            content=treatment_result.summary,
            timestamp=datetime.now(timezone.utc),
        )
    )
    state_store[request.session_id] = state

    return ApplyMissingValueSolutionResponse(
        session_id=request.session_id,
        phase=state.current_phase,
        dataset_profile=state.dataset_profile,
        dataset_summary_report=state.dataset_summary_report,
        missing_value_solutions=state.missing_value_solutions,
        last_missing_treatment_result=state.last_missing_treatment_result,
    )


@router.get("/state/{session_id}", response_model=StateResponse)
async def get_state(session_id: str):
    state = state_store.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return StateResponse(
        session_id=session_id,
        phase=state.current_phase,
        file_name=state.raw_file_name,
        shape=state.dataframe_shape,
        columns=state.dataframe_columns,
        file_size_mb=state.file_size_mb,
        dataset_profile=state.dataset_profile,
        domain_classification=state.domain_classification,
        dataset_summary_report=state.dataset_summary_report,
        intent_classification=state.intent_classification,
        analysis_plan=state.analysis_plan,
        execution_results=state.execution_results,
        hypothesis_set=state.hypothesis_set,
        parsed_intent=state.parsed_intent,
        target_column=state.target_column,
        target_type=state.target_type,
        generated_hypotheses=state.generated_hypotheses,
        statistical_results=state.statistical_results,
        ranked_drivers=state.ranked_drivers,
        final_answer=state.final_answer,
        legacy_statistical_results=state.driver_ranking.ranked_drivers if state.driver_ranking else [],
        driver_ranking=state.driver_ranking,
        driver_insight_report=state.driver_insight_report,
        missing_value_solutions=state.missing_value_solutions,
        last_missing_treatment_result=state.last_missing_treatment_result,
        conversation_history=state.conversation_history,
        errors=state.errors,
    )


@router.websocket("/ws/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """Execution event stream per active session."""
    await websocket.accept()
    active_connections[session_id] = websocket
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({"type": "heartbeat", "payload": {"session_id": session_id}})
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.pop(session_id, None)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.API_VERSION}
