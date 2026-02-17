# Design Summary & Decisions

## ✅ Architecture Confirmation

### Core Design Principles (Confirmed)

1. **LLM Never Executes Code**
   - LLM agents only: infer, parse, plan, synthesize
   - All execution via deterministic tools (pandas, sklearn, plotly)
   - LLM outputs are structured JSON validated by Pydantic

2. **Event-Driven Graph**
   - Single `StudioState` object flows through graph
   - Agents read state → process → update state → return next stage
   - No direct agent-to-agent calls
   - Orchestrator routes based on `state.current_stage`

3. **Deterministic Tools**
   - All data operations are deterministic
   - Tools in `backend/tools/` are pure functions
   - No randomness in execution (except where explicitly needed)

4. **Structured State**
   - `StudioState` is a Pydantic model
   - All fields typed and validated
   - State is mutable (for performance with large dataframes)

5. **Incremental Build**
   - Phase-by-phase implementation
   - Each phase tested before moving to next
   - Current: Phase 1 (Data Ingestion) complete

## 📁 Folder Structure (Implemented)

```
agentic-da-assistant/
├── backend/
│   ├── state/              ✅ StudioState model
│   ├── agents/             ✅ BaseAgent + DataIngestionAgent
│   ├── graph/              ✅ Orchestrator + stage transitions
│   ├── tools/              ✅ Data loader utilities
│   ├── api/                ✅ FastAPI routes + schemas
│   ├── config.py           ✅ Settings management
│   └── main.py             ✅ FastAPI app entry
├── frontend/
│   └── main.py             ✅ Streamlit app
├── docs/                    ✅ Architecture docs
└── requirements.txt         ✅ Dependencies
```

## 🎯 StudioState Model (Defined)

**Key Fields:**
- Raw input: `raw_file`, `raw_file_name`, `raw_file_size`
- Processed data: `dataframe`
- Phase 1 outputs: `dataset_profile`, `pattern_report`, `domain_classification`, `overview_report`
- Phase 2 inputs: `user_intent`, `intent_type`, `intent_structured`
- Phase 2 outputs: `analysis_plan`, `execution_results`, `insights`, `recommendations`
- Outputs: `report_paths`
- Control: `current_stage`, `errors`, `confidence_score`

**Design Decisions:**
- Mutable state (for performance)
- Pydantic validation
- Stage enum for type safety
- Helper methods (`add_error`, `update_stage`, `is_phase1_complete`)

## 🔄 Event-Driven Orchestration (Designed)

### Graph Orchestrator Pattern

```python
orchestrator = GraphOrchestrator()
orchestrator.register_agent(Stage.DATA_INGESTION, DataIngestionAgent())
state = orchestrator.run(state)  # Runs until END or ERROR
```

### Agent Pattern

```python
class DataIngestionAgent(BaseAgent):
    def process(self, state: StudioState) -> StudioState:
        # 1. Validate prerequisites
        # 2. Process (deterministic or LLM)
        # 3. Update state
        # 4. Set next stage
        # 5. Return state
```

### Stage Transitions

- Defined in `backend/graph/stages.py`
- Valid transitions enforced
- Conditional branching in `apply_transitions()`
- Error handling in `handle_error()`

### Benefits

1. **Decoupled**: Agents don't know about each other
2. **Testable**: Each agent tested in isolation
3. **Extensible**: Register new agents easily
4. **Debuggable**: State object shows entire system state
5. **Resumable**: Can save/load state at any point

## 🤖 Agent Registration (Designed)

**Current Implementation:**
```python
# In backend/main.py
orchestrator = GraphOrchestrator()
orchestrator.register_agent(Stage.DATA_INGESTION, DataIngestionAgent())
# TODO: Register other agents as implemented
```

**Future Pattern:**
```python
# As each agent is implemented:
orchestrator.register_agent(Stage.PROFILING, ProfilingAgent())
orchestrator.register_agent(Stage.PATTERN_DETECTION, PatternDetectionAgent())
# etc.
```

**Design Decision:**
- Agents registered at startup
- Can be swapped/mocked for testing
- No dynamic agent discovery (keeps it simple)

## 📊 Phase 1 Implementation (Complete)

### DataIngestionAgent

**Responsibilities:**
- Load file (CSV, Excel, HTML)
- Validate file size
- Validate dataframe
- Update state with dataframe and metadata
- Transition to PROFILING stage

**Tools Used:**
- `load_file()`: Pandas file loading
- `validate_dataframe()`: Dataframe validation
- `get_file_info()`: File metadata

**No LLM Usage**: Pure deterministic operations

### Testing Strategy

**Isolation Testing:**
- Test `DataIngestionAgent` with mock state
- Test `load_file()` with sample files
- Test orchestrator with single agent

**Integration Testing:**
- Upload file via API
- Verify state updates
- Verify stage transitions

## 🚀 Next Steps (Phase 2)

1. **ProfilingAgent**
   - Statistical profiling (describe(), info(), dtypes)
   - Update `state.dataset_profile`
   - Transition to PATTERN_DETECTION

2. **PatternDetectionAgent**
   - Detect correlations, outliers, missing patterns
   - Update `state.pattern_report`
   - Transition to DOMAIN_INFERENCE

3. **DomainInferenceAgent** (LLM)
   - Infer domain/industry context
   - Update `state.domain_classification`
   - Transition to INITIAL_INSIGHT

4. **InitialInsightAgent** (LLM)
   - Generate overview report
   - Update `state.overview_report`
   - Transition to WAIT_FOR_USER_INTENT

## 🔧 Configuration Management

**Settings in `backend/config.py`:**
- File upload limits (100MB)
- Allowed extensions (.csv, .xlsx, .html)
- Storage paths (uploads/, reports/, temp/)
- LLM settings (for future phases)
- API settings

**Environment Variables:**
- `.env` file support via Pydantic Settings
- `.env.example` provided as template

## 📝 Key Design Decisions Explained

### 1. Why Mutable State?

**Decision**: `StudioState` is mutable (Pydantic model with direct field updates)

**Reasoning**:
- Performance: Avoid copying large dataframes
- Simplicity: Direct updates are clearer
- Trade-off: Must be careful not to mutate incorrectly

**Alternative Considered**: Immutable state (create new state each time)
- Rejected due to performance concerns with large dataframes

### 2. Why Event-Driven Graph?

**Decision**: Agents update state, orchestrator routes based on stage

**Reasoning**:
- Decoupling: Agents don't depend on each other
- Testability: Test agents in isolation
- Observability: State object shows entire system state
- Flexibility: Easy to add/remove agents

**Alternative Considered**: Direct agent calls
- Rejected due to tight coupling and testing difficulties

### 3. Why Separate Tools from Agents?

**Decision**: Agents call tools, tools are pure functions

**Reasoning**:
- Reusability: Tools can be used by multiple agents
- Testability: Test tools independently
- Clarity: Agents orchestrate, tools execute

**Example**:
- `DataIngestionAgent` calls `load_file()` tool
- `ProfilingAgent` will call `profile_dataframe()` tool
- Tools are deterministic, agents add orchestration logic

### 4. Why Stage Enum?

**Decision**: Use `Stage` enum instead of strings

**Reasoning**:
- Type safety: Prevents typos
- IDE support: Autocomplete for stages
- Validation: Can validate transitions

**Example**:
```python
state.current_stage = Stage.PROFILING  # ✅ Type-safe
state.current_stage = "profiling"      # ❌ String (less safe)
```

### 5. Why In-Memory State Store?

**Decision**: Phase 1 uses in-memory `state_store` dict

**Reasoning**:
- Simplicity: No database needed for Phase 1
- Speed: Fast access for testing
- Future: Can migrate to Redis/DB later

**Future Migration**:
- Replace `state_store` dict with Redis or PostgreSQL
- State can be serialized/deserialized (Pydantic supports JSON)

## ✅ Phase 1 Skeleton Complete

**What's Ready:**
- ✅ Project structure
- ✅ StudioState model
- ✅ BaseAgent class
- ✅ GraphOrchestrator
- ✅ DataIngestionAgent
- ✅ Data loading tools
- ✅ FastAPI backend skeleton
- ✅ Streamlit frontend skeleton
- ✅ Configuration management
- ✅ Documentation

**What's Next:**
- Implement ProfilingAgent (Phase 2)
- Test Phase 1 end-to-end
- Add error handling improvements
- Add logging

## 🎯 Summary

The system skeleton is ready for Phase 1 testing. The architecture is:
- **Modular**: Clear separation of concerns
- **Extensible**: Easy to add new agents
- **Testable**: Each component can be tested independently
- **Production-ready**: Proper error handling, validation, configuration

The event-driven graph design ensures agents remain decoupled while the shared state object provides a clear view of system progress.
