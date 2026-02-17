"""
FastAPI application entry point.
"""

import sys
from pathlib import Path

# Add project root to path so "backend" package is found when running: python main.py
_project_root = Path(__file__).resolve().parent.parent
if _project_root not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import router
from backend.api.routes import websocket_session
from backend.config import settings

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Agentic Data Intelligence Studio - Multi-agent analytics system",
)

# CORS middleware (for Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["api"])
app.websocket("/ws/{session_id}")(websocket_session)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic Data Intelligence Studio API",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
