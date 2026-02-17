"""
Base agent class that all agents inherit from.

Agents are stateless - they process state and return updated state.
"""

from abc import ABC, abstractmethod
from typing import Optional
from backend.state import StudioState


class BaseAgent(ABC):
    """
    Base class for all agents.
    
    Agents follow this pattern:
    1. Read from state
    2. Process (deterministic or LLM)
    3. Update state with results
    4. Set next stage
    5. Return updated state
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def process(self, state: StudioState) -> StudioState:
        """
        Process the current state and return updated state.
        
        Args:
            state: Current StudioState
            
        Returns:
            Updated StudioState with results and next stage set
        """
        pass
    
    def validate_prerequisites(self, state: StudioState) -> tuple[bool, Optional[str]]:
        """
        Validate that prerequisites are met for this agent.
        
        Returns:
            (is_valid, error_message)
        """
        return True, None
    
    def log(self, message: str) -> None:
        """Log agent activity"""
        print(f"[{self.name}] {message}")
