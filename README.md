# Agentic Data Intelligence Studio

A production-style multi-agent AI system for Data Analyst and ML/AI roles.

## 🎯 Overview

This is a **goal-driven, event-driven, LangGraph-style multi-agent analytics system** for arbitrary structured datasets.

**Not** a simple EDA tool or ChatGPT-over-pandas wrapper. This is a serious, production-style system.

## 🏗️ Architecture

- **Backend**: FastAPI with event-driven graph orchestration
- **Frontend**: React (Vite + TypeScript)
- **State Management**: Single `StudioState` object flowing through graph
- **LLM Usage**: Only for reasoning/planning (not execution)
- **Execution**: Deterministic tools (pandas, scikit-learn, plotly)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

## 📁 Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for full structure.

Key directories:
- `backend/`: FastAPI backend, agents, graph orchestrator
- `frontend/`: React frontend (Vite, TypeScript)
- `backend/state/`: `StudioState` model
- `backend/agents/`: Agent implementations
- `backend/graph/`: Event-driven orchestrator
- `backend/tools/`: Deterministic tools

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- pip

### Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create `.env` file (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Running the Application

1. **Start Backend** (Terminal 1):
   ```bash
   cd backend
   python main.py
   ```
   API will be available at `http://localhost:8000`
   API docs at `http://localhost:8000/docs`

2. **Start Frontend** (Terminal 2):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend will be available at `http://localhost:5173` (Vite dev server proxies `/api` to the backend)

## 📊 Current Status

### ✅ Phase 1: Data Ingestion (COMPLETE)
- File upload (CSV, Excel, HTML)
- Data validation
- Basic state management
- Graph orchestrator skeleton

### 🚧 Phase 2: Profiling (TODO)
- Statistical profiling agent
- Pattern detection agent
- Domain inference agent (LLM)
- Initial insight agent (LLM)

### 🚧 Phase 3: Goal-Driven Analysis (TODO)
- Intent parser agent (LLM)
- Analysis planner agent (LLM)
- Execution engine agent
- Insight generator agent (LLM)
- Recommendation agent (LLM)
- Report generator agent
- Evaluation agent

## 🔷 Design Principles

1. **LLM Never Executes Code**: LLM only reasons, plans, synthesizes
2. **Deterministic Execution**: All data operations use pandas/scikit-learn directly
3. **Event-Driven Graph**: Agents update shared state, not direct calls
4. **Structured Outputs**: All agent outputs validated via Pydantic
5. **Incremental Build**: Phase-by-phase implementation with testing

