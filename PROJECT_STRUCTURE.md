# Project Structure

```
agentic-da-assistant/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration (file limits, paths, etc.)
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   └── studio_state.py     # StudioState Pydantic model
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Base agent class
│   │   ├── data_ingestion.py   # DataIngestionAgent (Phase 1)
│   │   ├── profiling.py        # ProfilingAgent (Phase 2)
│   │   ├── pattern_detection.py # PatternDetectionAgent (Phase 3)
│   │   ├── domain_inference.py # DomainInferenceAgent (Phase 4)
│   │   ├── initial_insight.py  # InitialInsightAgent (Phase 5)
│   │   ├── intent_parser.py    # IntentParserAgent (Phase 6)
│   │   ├── analysis_planner.py  # AnalysisPlannerAgent (Phase 7)
│   │   ├── execution_engine.py # ExecutionEngineAgent (Phase 8)
│   │   ├── insight_generator.py # InsightGeneratorAgent (Phase 9)
│   │   ├── recommendation.py   # RecommendationAgent (Phase 10)
│   │   ├── report_generator.py # ReportGeneratorAgent (Phase 11)
│   │   └── evaluation.py       # EvaluationAgent (Phase 12)
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Event-driven graph orchestrator
│   │   └── stages.py           # Stage constants and transitions
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── data_loader.py      # File loading utilities
│   │   ├── profiler.py         # Statistical profiling tools
│   │   ├── pattern_detector.py # Pattern detection tools
│   │   ├── ml_tools.py         # ML utilities (if needed)
│   │   └── visualization.py   # Plotly visualization tools
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py           # LLM client wrapper
│   │   └── prompts.py         # Prompt templates
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # FastAPI routes
│   │   └── schemas.py         # API request/response schemas
│   │
│   └── storage/
│       ├── __init__.py
│       ├── file_manager.py    # File upload/storage management
│       └── report_storage.py  # Report storage utilities
│
├── frontend/                   # React (Vite + TypeScript)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── types.ts
│       ├── api/
│       │   └── client.ts       # API client (upload, state, intent)
│       ├── context/
│       │   └── SessionContext.tsx
│       └── pages/
│           ├── Upload.tsx
│           ├── Dashboard.tsx
│           └── Reports.tsx
│
├── tests/
│   ├── __init__.py
│   ├── test_agents/
│   │   ├── test_data_ingestion.py
│   │   └── ...
│   ├── test_graph/
│   │   └── test_orchestrator.py
│   └── test_state/
│       └── test_studio_state.py
│
└── docs/
    ├── ARCHITECTURE.md        # This file
    └── API.md                 # API documentation
```

## Key Design Decisions

1. **Separation of Concerns**:
   - `agents/`: Agent logic (what to do)
   - `tools/`: Deterministic tools (how to do it)
   - `llm/`: LLM interaction (reasoning only)
   - `graph/`: Orchestration (when to do it)

2. **State Management**:
   - Single `StudioState` object in `state/`
   - All agents import and update same state class
   - State is passed through graph, not stored globally

3. **Agent Pattern**:
   - Base agent class with `process(state: StudioState) -> StudioState`
   - Each agent returns updated state and next stage
   - Agents are stateless (pure functions)

4. **Graph Orchestration**:
   - Event-driven: checks `state.current_stage`
   - Routes to appropriate agent
   - Handles errors and conditional branching

5. **File Organization**:
   - Backend and frontend separated
   - Tools isolated from agents
   - Tests mirror structure
