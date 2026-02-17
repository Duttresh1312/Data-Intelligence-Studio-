"""
DataIngestionAgent: Phase 1 - Loads and validates uploaded files.

This agent:
1. Loads file from raw_file path
2. Validates the dataframe
3. Updates state with dataframe and metadata
4. Transitions to PROFILING stage
"""

from pathlib import Path
from backend.state import StudioState, Stage
from backend.agents.base_agent import BaseAgent
from backend.tools import load_file, validate_dataframe, get_file_info
from backend.config import settings


class DataIngestionAgent(BaseAgent):
    """
    Agent responsible for loading and validating data files.
    
    This is a deterministic agent - no LLM usage.
    """
    
    def __init__(self):
        super().__init__(name="DataIngestionAgent")
    
    def validate_prerequisites(self, state: StudioState) -> tuple[bool, str | None]:
        """Validate that file path is available"""
        if state.raw_file is None:
            return False, "raw_file is None - no file to ingest"
        
        if not Path(state.raw_file).exists():
            return False, f"File does not exist: {state.raw_file}"
        
        return True, None
    
    def process(self, state: StudioState) -> StudioState:
        """
        Load file and validate dataframe.
        
        Updates:
        - state.dataframe
        - state.raw_file_name
        - state.raw_file_size
        - state.current_stage (to PROFILING or ERROR)
        """
        self.log(f"Processing file: {state.raw_file}")
        
        # Get file info
        file_info = get_file_info(Path(state.raw_file))
        state.raw_file_name = file_info["name"]
        state.raw_file_size = file_info["size_bytes"]
        
        # Check file size
        if file_info["size_bytes"] > settings.MAX_FILE_SIZE_BYTES:
            state.add_error(
                f"File too large: {file_info['size_mb']} MB "
                f"(max: {settings.MAX_FILE_SIZE_MB} MB)"
            )
            return state
        
        # Load file
        dataframe, error = load_file(Path(state.raw_file))
        
        if error:
            state.add_error(error)
            return state
        
        if dataframe is None:
            state.add_error("Failed to load dataframe")
            return state
        
        # Validate dataframe
        is_valid, validation_error = validate_dataframe(dataframe)
        
        if not is_valid:
            state.add_error(validation_error or "Dataframe validation failed")
            return state
        
        # Update state
        state.dataframe = dataframe
        state.current_stage = Stage.PROFILING
        
        self.log(f"Successfully ingested file: {state.raw_file_name}, shape: {dataframe.shape}")
        
        return state
