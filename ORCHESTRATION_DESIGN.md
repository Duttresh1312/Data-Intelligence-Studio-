# Event-Driven Orchestration Design

## Core Concept

The system uses an **event-driven graph** where:
1. **State object** (`StudioState`) flows through the graph
2. **Agents** read state, process, update state, return next stage
3. **Orchestrator** routes based on `state.current_stage`
4. **No direct agent-to-agent calls** - all communication via state

## Graph Orchestrator Pattern

```python
class GraphOrchestrator:
    def run(self, state: StudioState) -> StudioState:
        while state.current_stage != Stage.END:
            agent = self.get_agent_for_stage(state.current_stage)
            state = agent.process(state)
            
            # Handle errors
            if state.current_stage == Stage.ERROR:
                state = self.handle_error(state)
            
            # Conditional branching
            state = self.apply_transitions(state)
        
        return state
```

## Agent Interface

All agents follow this pattern:

```python
class BaseAgent:
    def process(self, state: StudioState) -> StudioState:
        """
        Process state and return updated state.
        
        Agents:
        1. Read from state
        2. Process (deterministic or LLM)
        3. Update state with results
        4. Set state.current_stage to next stage
        5. Return updated state
        """
        # Read from state
        if state.dataframe is None:
            state.add_error("Dataframe not available")
            return state
        
        # Process
        result = self._do_work(state)
        
        # Update state
        state.some_field = result
        state.current_stage = Stage.NEXT_STAGE
        
        return state
    
    def _do_work(self, state: StudioState) -> Any:
        """Agent-specific logic"""
        raise NotImplementedError
```

## Stage Transitions

### Phase 1: Autonomous Understanding
```
START
  → DATA_INGESTION (always)
  → PROFILING (if ingestion success)
  → PATTERN_DETECTION (if profiling success)
  → DOMAIN_INFERENCE (if pattern detection success)
  → INITIAL_INSIGHT (if domain inference success)
  → WAIT_FOR_USER_INTENT (if all Phase 1 complete)
```

### Phase 2: Goal-Driven Analysis
```
WAIT_FOR_USER_INTENT
  → INTENT_PARSING (when user intent received)
  → ANALYSIS_PLANNING (if intent parsed)
  → EXECUTION (if plan created)
  → INSIGHT_GENERATION (if execution success)
  → RECOMMENDATION (if insights generated)
  → REPORT_GENERATION (if recommendations ready)
  → EVALUATION (if report generated)
  → END (if evaluation complete)
```

## Conditional Branching

The orchestrator can handle conditional transitions:

```python
def apply_transitions(self, state: StudioState) -> StudioState:
    """Apply conditional transitions based on state"""
    
    # Example: Replan if execution fails
    if state.current_stage == Stage.EXECUTION:
        if state.execution_results and any(r.get('failed') for r in state.execution_results):
            # Loop back to planner
            state.current_stage = Stage.ANALYSIS_PLANNING
            state.errors.append("Execution failed, replanning...")
    
    # Example: Skip ML if not requested
    if state.current_stage == Stage.EXECUTION:
        if state.intent_type != IntentType.PREDICTIVE:
            # Skip ML steps in plan
            state.analysis_plan = [s for s in state.analysis_plan if 'ml' not in s.get('type', '')]
    
    return state
```

## Error Handling

Errors are captured in `state.errors`:

```python
def handle_error(self, state: StudioState) -> StudioState:
    """Handle errors based on stage"""
    
    if state.current_stage == Stage.DATA_INGESTION:
        # Cannot recover from ingestion failure
        state.current_stage = Stage.END
        return state
    
    elif state.current_stage == Stage.EXECUTION:
        # Can replan
        state.current_stage = Stage.ANALYSIS_PLANNING
        return state
    
    # Default: log and continue to next stage
    return state
```

## Agent Registration

Agents are registered in the orchestrator:

```python
class GraphOrchestrator:
    def __init__(self):
        self.agents = {
            Stage.DATA_INGESTION: DataIngestionAgent(),
            Stage.PROFILING: ProfilingAgent(),
            Stage.PATTERN_DETECTION: PatternDetectionAgent(),
            # ... etc
        }
    
    def get_agent_for_stage(self, stage: Stage) -> BaseAgent:
        agent = self.agents.get(stage)
        if agent is None:
            raise ValueError(f"No agent registered for stage: {stage}")
        return agent
```

## Benefits of This Design

1. **Decoupled**: Agents don't know about each other
2. **Testable**: Each agent can be tested in isolation
3. **Extensible**: Add new agents by registering them
4. **Debuggable**: State object shows entire system state
5. **Resumable**: Can save/load state at any point
6. **Observable**: Can log state transitions for monitoring

## State Immutability Consideration

**Current Design**: State is mutable (Pydantic model)

**Alternative**: Immutable state (create new state each time)

We use mutable state for:
- Simplicity
- Performance (avoid copying large dataframes)
- Direct updates

Trade-off: Must be careful not to mutate state incorrectly.
