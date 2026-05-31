"""
TODO management tool for tracking daily tasks and assignments.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from agentic_os.config import get_settings
from agentic_os.tools.base import Tool, ToolInput, ToolOutput


class TODOItem(BaseModel):
    """A single TODO item."""
    id: str
    task: str
    priority: str = "normal"
    status: str = "pending"  # pending, completed
    created_at: str
    completed_at: Optional[str] = None


class TODOAddInput(ToolInput):
    """Input for adding a TODO."""
    task: str = Field(description="The task description")
    priority: str = Field(default="normal", description="Task priority (low, normal, high)")


class TODOListInput(ToolInput):
    """Input for listing TODOs."""
    status: str = Field(default="pending", description="Filter by status (pending, completed, all)")


class TODOCompleteInput(ToolInput):
    """Input for completing a TODO."""
    todo_id: str = Field(description="The unique ID of the TODO to complete")


class TODOTool(Tool):
    """Tool for managing daily TODOs and tasks."""

    def __init__(self):
        super().__init__(
            name="todo_manage",
            description="Manage daily tasks and TODOs (add, list, complete)",
        )
        self.settings = get_settings()
        self.todo_file = self.settings.data_dir / "todos.json"

    @property
    def input_schema(self) -> type[ToolInput]:
        return TODOAddInput  # Default schema, but execute handles others via kwargs

    @property
    def output_schema(self) -> type[ToolOutput]:
        return ToolOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        action = kwargs.get("action", "add")
        
        if action == "add":
            return await self._add_todo(kwargs.get("task"), kwargs.get("priority", "normal"))
        elif action == "list":
            return await self._list_todos(kwargs.get("status", "pending"))
        elif action == "complete":
            return await self._complete_todo(kwargs.get("todo_id"))
        
        return ToolOutput(success=False, error=f"Unknown action: {action}")

    async def _add_todo(self, task: str, priority: str) -> ToolOutput:
        if not task:
            return ToolOutput(success=False, error="Task description is required")
            
        todos = self._load_todos()
        new_todo = {
            "id": str(uuid4())[:8],
            "task": task,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        todos.append(new_todo)
        self._save_todos(todos)
        
        return ToolOutput(success=True, data=new_todo)

    async def _list_todos(self, status: str) -> ToolOutput:
        todos = self._load_todos()
        if status != "all":
            todos = [t for t in todos if t["status"] == status]
            
        return ToolOutput(success=True, data={"todos": todos, "count": len(todos)})

    async def _complete_todo(self, todo_id: str) -> ToolOutput:
        todos = self._load_todos()
        found = False
        for t in todos:
            if t["id"] == todo_id:
                t["status"] = "completed"
                t["completed_at"] = datetime.now(timezone.utc).isoformat()
                found = True
                break
        
        if not found:
            return ToolOutput(success=False, error=f"TODO with ID {todo_id} not found")
            
        self._save_todos(todos)
        return ToolOutput(success=True, data={"completed_id": todo_id})

    def _load_todos(self) -> List[dict]:
        if not self.todo_file.exists():
            return []
        try:
            return json.loads(self.todo_file.read_text())
        except Exception:
            return []

    def _save_todos(self, todos: List[dict]):
        self.todo_file.write_text(json.dumps(todos, indent=2))
