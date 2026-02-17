# Agentic Data Intelligence Studio - Architecture

## Core Design Principles

1. **LLM Never Executes Code**: LLM only reasons, plans, and synthesizes
2. **Deterministic Execution**: All data operations use pandas/scikit-learn directly
3. **Event-Driven Graph**: Agents update shared state, not direct calls
4. **Structured Outputs**: All agent outputs validated via Pydantic
5. **Incremental Build**: Phase-by-phase implementation with testing

## State Flow

```
StudioState (shared state object)
    ↓
Agents read state → process → update state
    ↓
Graph orchestrates transitions based on state.current_stage
```

## Graph Structure

### Phase 1: Autonomous Understanding
```
START
  → DataIngestionAgent (loads file, creates dataframe)
  → ProfilingAgent (statistical profiling)
  → PatternDetectionAgent (detects patterns)
  → DomainInferenceAgent (LLM: infers domain context)
  → InitialInsightAgent (LLM: generates overview)
  → WAIT_FOR_USER_INTENT
```

### Phase 2: Goal-Driven Analysis
```
User Intent Received
  → IntentParserAgent (LLM: parses intent)
  → AnalysisPlannerAgent (LLM: creates plan)
  → ExecutionEngineAgent (deterministic: executes tools)
  → InsightGeneratorAgent (LLM: synthesizes insights)
  → RecommendationAgent (LLM: generates recommendations)
  → ReportGeneratorAgent (creates PDF/HTML/CSV/Excel)
  → EvaluationAgent (evaluates quality)
  → END
```

## Agent Responsibilities

### LLM Agents (Reasoning Only)
- **DomainInferenceAgent**: Infers business domain from data
- **IntentParserAgent**: Parses user intent into structured format
- **AnalysisPlannerAgent**: Creates step-by-step analysis plan
- **InsightGeneratorAgent**: Synthesizes findings into insights
- **RecommendationAgent**: Generates actionable recommendations

### Deterministic Agents (No LLM)
- **DataIngestionAgent**: Loads and validates files
- **ProfilingAgent**: Statistical profiling (pandas describe, etc.)
- **PatternDetectionAgent**: Pattern detection (correlations, outliers, etc.)
- **ExecutionEngineAgent**: Executes analysis tools (pandas, sklearn, plotly)
- **ReportGeneratorAgent**: Generates reports (PDF, HTML, CSV, Excel)
- **EvaluationAgent**: Evaluates analysis quality

## State Management

All agents:
1. Read from `StudioState`
2. Process based on current stage
3. Update `StudioState` with results
4. Return next stage or `END`

Graph orchestrator:
- Monitors `current_stage`
- Routes to appropriate agent
- Handles errors and replanning
