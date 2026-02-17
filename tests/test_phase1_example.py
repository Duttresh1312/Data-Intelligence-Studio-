"""
Example test for Phase 1: Data Ingestion

This demonstrates how to test the DataIngestionAgent in isolation.
"""

import pytest
from pathlib import Path
import pandas as pd
from backend.state import StudioState, Stage
from backend.agents import DataIngestionAgent
from backend.graph import GraphOrchestrator


def test_data_ingestion_agent():
    """Test DataIngestionAgent with a sample CSV file"""
    
    # Create a sample CSV file for testing
    test_data = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'score': [85.5, 90.0, 88.5]
    })
    
    test_file = Path("data/temp/test_sample.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    # Create initial state
    state = StudioState(
        raw_file=test_file,
        current_stage=Stage.START,
    )
    
    # Create agent
    agent = DataIngestionAgent()
    
    # Process state
    state = agent.process(state)
    
    # Assertions
    assert state.dataframe is not None
    assert len(state.dataframe) == 3
    assert state.raw_file_name == "test_sample.csv"
    assert state.current_stage == Stage.PROFILING
    assert len(state.errors) == 0
    
    # Cleanup
    test_file.unlink()


def test_orchestrator_with_data_ingestion():
    """Test orchestrator with DataIngestionAgent"""
    
    # Create sample file
    test_data = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
    test_file = Path("data/temp/test_orchestrator.csv")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_data.to_csv(test_file, index=False)
    
    # Create state
    state = StudioState(
        raw_file=test_file,
        current_stage=Stage.START,
    )
    
    # Create orchestrator and register agent
    orchestrator = GraphOrchestrator()
    orchestrator.register_agent(Stage.DATA_INGESTION, DataIngestionAgent())
    
    # Run (will stop at PROFILING since no agent registered)
    state = orchestrator.run(state)
    
    # Assertions
    assert state.dataframe is not None
    assert state.current_stage == Stage.PROFILING  # Next stage
    
    # Cleanup
    test_file.unlink()


if __name__ == "__main__":
    # Run tests manually
    test_data_ingestion_agent()
    test_orchestrator_with_data_ingestion()
    print("✅ All tests passed!")
