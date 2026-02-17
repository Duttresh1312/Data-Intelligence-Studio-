"""
Stage definitions and transition logic for the graph orchestrator.
"""

from backend.state import Stage


# Define valid transitions
STAGE_TRANSITIONS = {
    Stage.START: [Stage.DATA_INGESTION],
    Stage.DATA_INGESTION: [Stage.PROFILING, Stage.ERROR],
    Stage.PROFILING: [Stage.PATTERN_DETECTION, Stage.ERROR],
    Stage.PATTERN_DETECTION: [Stage.DOMAIN_INFERENCE, Stage.ERROR],
    Stage.DOMAIN_INFERENCE: [Stage.INITIAL_INSIGHT, Stage.ERROR],
    Stage.INITIAL_INSIGHT: [Stage.WAIT_FOR_USER_INTENT, Stage.ERROR],
    Stage.WAIT_FOR_USER_INTENT: [Stage.INTENT_PARSING, Stage.END],
    Stage.INTENT_PARSING: [Stage.ANALYSIS_PLANNING, Stage.ERROR],
    Stage.ANALYSIS_PLANNING: [Stage.EXECUTION, Stage.ERROR],
    Stage.EXECUTION: [Stage.INSIGHT_GENERATION, Stage.ANALYSIS_PLANNING, Stage.ERROR],  # Can replan
    Stage.INSIGHT_GENERATION: [Stage.RECOMMENDATION, Stage.ERROR],
    Stage.RECOMMENDATION: [Stage.REPORT_GENERATION, Stage.ERROR],
    Stage.REPORT_GENERATION: [Stage.EVALUATION, Stage.ERROR],
    Stage.EVALUATION: [Stage.END, Stage.ERROR],
    Stage.ERROR: [Stage.END],  # Terminal error state
    Stage.END: [],  # Terminal state
}


def is_valid_transition(from_stage: Stage, to_stage: Stage) -> bool:
    """Check if transition from one stage to another is valid"""
    valid_next = STAGE_TRANSITIONS.get(from_stage, [])
    return to_stage in valid_next


def get_next_stages(current_stage: Stage) -> list[Stage]:
    """Get list of valid next stages from current stage"""
    return STAGE_TRANSITIONS.get(current_stage, [])
