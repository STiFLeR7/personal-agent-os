"""
FastAPI Backend for Dex Dashboard.

This module provides REST endpoints for the Next.js frontend to interact with
Dex's state, memory, and telemetry.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import uvicorn

from agentic_os.core.state import get_state_manager
from agentic_os.core.telemetry import TelemetryManager
from agentic_os.core.memory import ContextMemoryEngine
from agentic_os.config import get_settings

app = FastAPI(title="Dex Cognitive OS API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state_manager = get_state_manager()
telemetry = TelemetryManager()
memory = ContextMemoryEngine()

@app.get("/")
async def root():
    return {"status": "online", "agent": "Dex Cognitive OS"}

@app.get("/telemetry/summary")
async def get_telemetry_summary():
    return telemetry.get_metrics_summary()

@app.get("/state/system")
async def get_system_state():
    return state_manager.get_system_state().model_dump()

@app.get("/memory/search")
async def search_memory(q: str, semantic: bool = True):
    if semantic:
        return [m.model_dump() for m in memory.search_semantic(q)]
    return [m.model_dump() for m in memory.search(q)]

@app.get("/tasks/active")
async def get_active_tasks():
    active_ids = state_manager.get_active_tasks()
    tasks = []
    for tid in active_ids:
        exec_state = state_manager.get_execution_state(tid)
        if exec_state:
            tasks.append(exec_state.model_dump())
    return tasks

def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI server."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
