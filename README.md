# Agentic Data Intelligence Studio

Agentic Data Intelligence Studio is a goal-driven analytics platform designed for structured datasets. It combines deterministic statistical computation with controlled LLM reasoning to deliver evidence-based insights instead of generic summaries.

The system is built for data analysts and ML practitioners who want structured, explainable, and repeatable analysis workflows — not chatbot-style exploration.

---

## What This Project Does

This platform allows a user to:

- Upload structured datasets (CSV, Excel, HTML) up to 100MB  
- Automatically profile and assess data quality  
- Detect missing value issues and apply deterministic treatments  
- Classify dataset domain and structure  
- Ask analysis questions in natural language  
- Run statistical driver analysis on selected outcome variables  
- Receive structured, evidence-backed insights  

The system separates computation from reasoning:

- All statistics, correlations, hypothesis testing, and modeling are deterministic (pandas, scipy, scikit-learn).
- LLMs are used only for intent classification, structured reasoning, and insight synthesis.
- No raw data is ever processed inside the LLM.

---

## Core Design Principles

- Deterministic analytics first  
- Strict typed outputs (Pydantic models)  
- State-driven workflow using phase transitions  
- Modular agent architecture  
- Clear separation between computation and explanation  
- Production-style API structure  

This is not an exploratory notebook replacement.  
It is a structured analytics engine with progressive state transitions.

---

## High-Level Workflow

1. Upload dataset  
2. Data ingestion and profiling  
3. Domain inference and dataset summary  
4. Missing value treatment loop  
5. User submits analytical goal  
6. System parses intent and detects target variable  
7. Deterministic statistical testing and driver ranking  
8. Structured insight synthesis  

Each stage updates a controlled session state model.

---

## Tech Stack

### Backend
- FastAPI  
- Pydantic v2  
- pandas  
- scipy  
- scikit-learn  
- OpenAI-compatible LLM SDK  

### Frontend
- React  
- TypeScript  
- Vite  
- Tailwind CSS  
- Recharts  

---

## Project Structure

backend/
frontend/
data/
tests/


Key backend components:

- `state.py` — central session state model  
- `graph.py` — phase orchestration  
- `profiling.py` — deterministic dataset profiling  
- `missing_value_treatment.py` — treatment engine  
- `intent_parser.py` — structured intent detection  
- `statistical_engine.py` — hypothesis testing  
- `driver_ranking.py` — feature strength scoring  
- `insight_synthesis.py` — structured explanation layer  

---

## Running the Project

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python backend/main.py

``` 

### Frontend

```bash
cd frontend
npm install
npm run dev

```

---

## Environment Configuration

Key environment variables:

- USE_LLM
- LLM_PROVIDER
- LLM_MODEL
- LLM_BASE_URL
- LLM_API_KEY
- MAX_FILE_SIZE_MB
- UPLOAD_DIR
- REPORTS_DIR

See .env for reference.

