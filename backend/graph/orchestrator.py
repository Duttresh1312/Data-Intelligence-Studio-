"""
Event-driven graph orchestrator.

Routes state through agents based on current_stage.
Handles errors and conditional branching.
"""

from typing import Dict, Optional
from backend.state import StudioState, Stage
from backend.agents.base_agent import BaseAgent
from backend.graph.stages import is_valid_transition


class GraphOrchestrator:
    """
    Orchestrates the event-driven graph execution.
    
    Routes state through agents based on state.current_stage.
    Handles errors, conditional branching, and replanning.
    """
    
    def __init__(self):
        self.agents: Dict[Stage, BaseAgent] = {}
        self.max_iterations = 100  # Prevent infinite loops
    
    def register_agent(self, stage: Stage, agent: BaseAgent) -> None:
        """Register an agent for a specific stage"""
        self.agents[stage] = agent
    
    def get_agent_for_stage(self, stage: Stage) -> Optional[BaseAgent]:
        """Get agent for a specific stage"""
        return self.agents.get(stage)
    
    def run(self, state: StudioState) -> StudioState:
        """
        Run the graph until completion or error.
        
        Args:
            state: Initial StudioState
            
        Returns:
            Final StudioState (END or ERROR)
        """
        iteration = 0
        
        while state.current_stage != Stage.END and iteration < self.max_iterations:
            iteration += 1
            
            # Get agent for current stage
            agent = self.get_agent_for_stage(state.current_stage)
            
            if agent is None:
                state.add_error(f"No agent registered for stage: {state.current_stage}")
                break
            
            # Validate prerequisites
            is_valid, error_msg = agent.validate_prerequisites(state)
            if not is_valid:
                state.add_error(error_msg or f"Prerequisites not met for {state.current_stage}")
                break
            
            # Process state
            try:
                previous_stage = state.current_stage
                state = agent.process(state)
                
                # Validate transition
                if not is_valid_transition(previous_stage, state.current_stage):
                    state.add_error(
                        f"Invalid transition: {previous_stage} -> {state.current_stage}"
                    )
                    break
                
                # Handle errors
                if state.current_stage == Stage.ERROR:
                    state = self.handle_error(state, previous_stage)
                
                # Apply conditional transitions
                state = self.apply_transitions(state)
                
            except Exception as e:
                state.add_error(f"Error in {agent.name}: {str(e)}")
                break
        
        if iteration >= self.max_iterations:
            state.add_error("Maximum iterations reached - possible infinite loop")
        
        return state
    
    def handle_error(self, state: StudioState, previous_stage: Stage) -> StudioState:
        """
        Handle errors based on stage and context.
        
        Some errors are recoverable (e.g., replanning),
        others are terminal (e.g., data ingestion failure).
        """
        # Terminal errors - cannot recover
        if previous_stage in [Stage.DATA_INGESTION]:
            state.current_stage = Stage.END
            return state
        
        # Recoverable errors - can replan
        if previous_stage == Stage.EXECUTION:
            # Execution failed - try replanning
            state.current_stage = Stage.ANALYSIS_PLANNING
            state.errors.append("Execution failed, attempting replanning...")
            return state
        
        # Default: log error and end
        state.current_stage = Stage.END
        return state
    
    def apply_transitions(self, state: StudioState) -> StudioState:
        """
        Apply conditional transitions based on state.
        
        This is where we handle:
        - Skipping steps based on intent type
        - Replanning logic
        - Conditional branching
        """
        # Example: Skip ML if not predictive intent
        if state.current_stage == Stage.ANALYSIS_PLANNING:
            if state.intent_type and state.intent_type.value != "PREDICTIVE":
                # Filter out ML steps if plan already exists
                if state.analysis_plan:
                    state.analysis_plan = [
                        step for step in state.analysis_plan
                        if 'ml' not in step.get('type', '').lower()
                    ]
        
        return state
