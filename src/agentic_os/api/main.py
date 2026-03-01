"""
FastAPI Backend for Dex Dashboard.

This module provides REST endpoints for the Next.js frontend to interact with
Dex's state, memory, and telemetry.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import uvicorn
import asyncio
from uuid import uuid4
from pydantic import BaseModel

from agentic_os.core.state import get_state_manager
from agentic_os.core.telemetry import TelemetryManager
from agentic_os.core.memory import ContextMemoryEngine
from agentic_os.config import get_settings
from agentic_os.coordination import TaskDefinition, get_bus, Message, MessageType
from agentic_os.core import PlannerAgent, ExecutorAgent, VerifierAgent
from agentic_os.tools.base import get_tool_registry
from agentic_os.tools import (
    ShellCommandTool, FileReadTool, FileWriteTool, NoteCreateTool, NoteListTool,
    ReminderSetTool, ReminderListTool, EmailComposeTool, BrowserOpenTool, AppLaunchTool
)

app = FastAPI(title="Dex Cognitive OS API")

class TaskRequest(BaseModel):
    request: str

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import json
from pathlib import Path

state_manager = get_state_manager()
telemetry = TelemetryManager()
memory = ContextMemoryEngine()

@app.get("/")
async def root():
    return {"status": "online", "agent": "Dex Cognitive Bot"}

@app.get("/health")
async def health():
    """Endpoint for Render to check if the service is alive."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/reminders")
async def get_reminders():
    settings = get_settings()
    reminders_file = settings.data_dir / "reminders.json"
    if not reminders_file.exists():
        return []
    with open(reminders_file, "r") as f:
        return json.load(f)

@app.get("/notes")
async def get_notes():
    settings = get_settings()
    notes_dir = settings.data_dir / "notes"
    if not notes_dir.exists():
        return []
    notes = []
    for file in notes_dir.glob("*.md"):
        notes.append({
            "filename": file.name,
            "content": file.read_text(encoding="utf-8")[:200] + "...",
            "path": str(file)
        })
    return notes

@app.get("/config")
async def get_system_config():
    settings = get_settings()
    return {
        "llm_provider": settings.llm.provider,
        "llm_model": settings.llm.model_name,
        "discord_enabled": (
            settings.discord.webhook_url is not None
            or settings.llm.discord_webhook_url is not None
        ),
        "debug_mode": settings.debug_mode
    }

@app.get("/modes")
async def get_modes():
    # Hardcoded for now, could be in settings
    return [
        {"id": "deep-work", "name": "Deep Work", "active": True, "color": "#34C759"},
        {"id": "privacy-plus", "name": "Privacy+", "active": False, "color": "#0A84FF"},
        {"id": "research", "name": "Research", "active": False, "color": "#AF52DE"}
    ]

@app.post("/tasks/run")
async def run_task(task_req: TaskRequest):
    """Execute a task in the background."""
    # This is a simplified version of _execute_task from cli.py
    # Ideally, agents would be running in a persistent daemon process.
    # For now, we'll spin them up per request to ensure it works.
    
    request = task_req.request
    
    async def _bg_execute():
        bus = await get_bus()
        registry = get_tool_registry()
        
        # Register tools
        tools = [
            ShellCommandTool(), FileReadTool(), FileWriteTool(), NoteCreateTool(),
            NoteListTool(), ReminderSetTool(), ReminderListTool(), EmailComposeTool(),
            BrowserOpenTool(), AppLaunchTool()
        ]
        for tool in tools:
            try: registry.register(tool)
            except ValueError: pass

        planner = PlannerAgent()
        executor = ExecutorAgent()
        verifier = VerifierAgent()

        await planner.initialize(bus)
        await executor.initialize(bus)
        await verifier.initialize(bus)

        task = TaskDefinition(id=uuid4(), user_request=request)
        
        # In this mode, we skip the human-confirmation for now to make it autonomous
        # But we could implement a websocket or polling for confirmation.
        
        plan_request = Message(
            message_type=MessageType.PLAN_REQUEST,
            sender="api",
            recipient="planner",
            payload={"task": task.model_dump()},
        )

        try:
            plan_response = await bus.request_response(plan_request, timeout_seconds=30)
            plan_data = plan_response.payload.get("plan")
            if plan_data:
                execute_request = Message(
                    message_type=MessageType.EXECUTE_REQUEST,
                    sender="api",
                    recipient="executor",
                    payload={"plan": plan_data, "task_id": str(task.id)},
                )
                await bus.publish(execute_request)
        except Exception as e:
            print(f"Error executing task in background: {e}")
        finally:
            # We don't shutdown immediately to allow background tasks to finish
            # In a real daemon, this wouldn't be needed.
            await asyncio.sleep(60) 
            await planner.shutdown()
            await executor.shutdown()
            await verifier.shutdown()

    asyncio.create_task(_bg_execute())
    return {"status": "accepted", "message": "Task execution started in background"}

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

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
