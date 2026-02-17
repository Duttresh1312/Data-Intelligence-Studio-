"""
StudioState: Central state object for the entire multi-agent system.

All agents read from and update this state object.
The graph orchestrator uses current_stage to route to appropriate agents.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field, field_validator


class Stage(str, Enum):
    """Pipeline stages - controls graph flow"""
    START = "START"
    DATA_INGESTION = "DATA_INGESTION"
    PROFILING = "PROFILING"
    PATTERN_DETECTION = "PATTERN_DETECTION"
    DOMAIN_INFERENCE = "DOMAIN_INFERENCE"
    INITIAL_INSIGHT = "INITIAL_INSIGHT"
    WAIT_FOR_USER_INTENT = "WAIT_FOR_USER_INTENT"
    INTENT_PARSING = "INTENT_PARSING"
    ANALYSIS_PLANNING = "ANALYSIS_PLANNING"
    EXECUTION = "EXECUTION"
    INSIGHT_GENERATION = "INSIGHT_GENERATION"
    RECOMMENDATION = "RECOMMENDATION"
    REPORT_GENERATION = "REPORT_GENERATION"
    EVALUATION = "EVALUATION"
    END = "END"
    ERROR = "ERROR"


class IntentType(str, Enum):
    """Types of user intents"""
    EXPLORATORY = "EXPLORATORY"
    PREDICTIVE = "PREDICTIVE"
    DESCRIPTIVE = "DESCRIPTIVE"
    DIAGNOSTIC = "DIAGNOSTIC"
    PRESCRIPTIVE = "PRESCRIPTIVE"
    UNKNOWN = "UNKNOWN"


class StudioState(BaseModel):
    """
    Central state object that flows through the entire graph.
    
    All agents read from and update this state.
    The graph orchestrator routes based on current_stage.
    """
    
    # Raw input
    raw_file: Optional[Path] = Field(default=None, description="Path to uploaded file")
    raw_file_name: Optional[str] = Field(default=None, description="Original filename")
    raw_file_size: Optional[int] = Field(default=None, description="File size in bytes")
    
    # Processed data
    dataframe: Optional[pd.DataFrame] = Field(default=None, description="Loaded dataframe")
    
    # Phase 1: Autonomous Understanding
    dataset_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Statistical profile (describe(), info(), dtypes, etc.)"
    )
    pattern_report: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detected patterns (correlations, outliers, missing patterns, etc.)"
    )
    domain_classification: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Inferred domain/industry context (LLM-generated)"
    )
    overview_report: Optional[str] = Field(
        default=None,
        description="Initial overview insights (LLM-generated)"
    )
    
    # Phase 2: Goal-Driven Analysis
    user_intent: Optional[str] = Field(
        default=None,
        description="Raw user intent text"
    )
    intent_type: Optional[IntentType] = Field(
        default=None,
        description="Parsed intent type"
    )
    intent_structured: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured intent representation (LLM-parsed)"
    )
    analysis_plan: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Step-by-step analysis plan (LLM-generated)"
    )
    execution_results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Results from each execution step"
    )
    insights: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Generated insights (LLM-synthesized)"
    )
    recommendations: Optional[List[str]] = Field(
        default=None,
        description="Actionable recommendations (LLM-generated)"
    )
    
    # Outputs
    report_paths: Optional[Dict[str, Path]] = Field(
        default=None,
        description="Paths to generated reports (PDF, HTML, CSV, Excel)"
    )
    
    # Quality & Control
    evaluation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Self-evaluation of analysis quality"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0-1)"
    )
    current_stage: Stage = Field(
        default=Stage.START,
        description="Current pipeline stage (controls graph routing)"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of errors encountered"
    )
    
    # Metadata
    session_id: Optional[str] = Field(
        default=None,
        description="Unique session identifier"
    )
    created_at: Optional[str] = Field(
        default=None,
        description="Timestamp of state creation"
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="Timestamp of last update"
    )
    
    class Config:
        """Pydantic config for pandas DataFrame support"""
        arbitrary_types_allowed = True
        json_encoders = {
            pd.DataFrame: lambda df: df.to_dict('records') if df is not None else None,
            Path: str,
        }
    
    @field_validator('dataframe', mode='before')
    @classmethod
    def validate_dataframe(cls, v):
        """Allow None or DataFrame"""
        if v is None or isinstance(v, pd.DataFrame):
            return v
        raise ValueError("dataframe must be None or pandas DataFrame")
    
    def add_error(self, error: str) -> None:
        """Helper to add error message"""
        self.errors.append(error)
        self.current_stage = Stage.ERROR
    
    def update_stage(self, stage: Stage) -> None:
        """Helper to update stage"""
        self.current_stage = stage
    
    def is_phase1_complete(self) -> bool:
        """Check if Phase 1 (autonomous understanding) is complete"""
        return (
            self.dataframe is not None
            and self.dataset_profile is not None
            and self.pattern_report is not None
            and self.domain_classification is not None
            and self.overview_report is not None
        )
    
    def is_phase2_complete(self) -> bool:
        """Check if Phase 2 (goal-driven analysis) is complete"""
        return (
            self.user_intent is not None
            and self.analysis_plan is not None
            and self.execution_results is not None
            and self.insights is not None
            and self.recommendations is not None
            and self.report_paths is not None
        )
