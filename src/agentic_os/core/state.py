"""
State management for the agentic system.

This module handles persistent and working state, including:
- Task state and execution results
- Agent state snapshots
- Context for ongoing operations
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ContextFrame(BaseModel):
    """A frame of context for task execution."""

    name: str = Field(description="Context name (e.g., 'user_request', 'environment')")
    data: Dict[str, Any] = Field(default_factory=dict, description="Context data")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(
        default=None, description="When this context expires (None = never)"
    )
    immutable: bool = Field(
        default=False, description="Whether context can be modified"
    )

    def is_expired(self) -> bool:
        """Check if this context has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class ExecutionTrace(BaseModel):
    """Complete trace of a task's execution."""

    task_id: Optional[UUID] = Field(default=None, description="ID of executed task")
    status: str = Field(default="pending", description="Task status")
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    steps_executed: List[Dict[str, Any]] = Field(
        default_factory=list, description="Ordered list of executed steps"
    )
    decisions_made: List[Dict[str, Any]] = Field(
        default_factory=list, description="Reasoning decisions"
    )
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Errors encountered"
    )
    final_result: Optional[Dict[str, Any]] = Field(
        default=None, description="Final outcome of task"
    )

    def duration_seconds(self) -> Optional[float]:
        """Get total execution time in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class ExecutionState(BaseModel):
    """Runtime state for a task execution."""

    task_id: UUID = Field(description="Task being executed")
    agent_id: str = Field(description="Agent currently executing")
    context_frames: List[ContextFrame] = Field(
        default_factory=list, description="Stack of context frames"
    )
    execution_trace: ExecutionTrace = Field(
        default_factory=ExecutionTrace, description="Execution history"
    )
    iteration: int = Field(default=0, description="Current iteration number")
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Runtime variables"
    )

    def push_context(self, name: str, data: Dict[str, Any]) -> None:
        """Push a new context frame."""
        self.context_frames.append(
            ContextFrame(name=name, data=data.copy())
        )

    def pop_context(self) -> Optional[ContextFrame]:
        """Pop a context frame."""
        return self.context_frames.pop() if self.context_frames else None

    def get_context(self, name: str) -> Optional[Dict[str, Any]]:
        """Get context by name (most recent first)."""
        for frame in reversed(self.context_frames):
            if frame.name == name and not frame.is_expired():
                return frame.data
        return None

    def set_variable(self, name: str, value: Any) -> None:
        """Set a runtime variable."""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a runtime variable."""
        return self.variables.get(name, default)


class SystemState(BaseModel):
    """Overall system state snapshot."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_tasks: List[UUID] = Field(default_factory=list, description="Currently executing tasks")
    agent_states: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="State of each agent"
    )
    execution_states: Dict[UUID, ExecutionState] = Field(
        default_factory=dict, description="Execution state per task"
    )
    global_context: Dict[str, Any] = Field(
        default_factory=dict, description="System-wide context"
    )

    def register_task(self, task_id: UUID, agent_id: str) -> ExecutionState:
        """Register a new task execution."""
        self.active_tasks.append(task_id)
        state = ExecutionState(task_id=task_id, agent_id=agent_id)
        self.execution_states[task_id] = state
        return state

    def unregister_task(self, task_id: UUID) -> None:
        """Mark a task as complete."""
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
        if task_id in self.execution_states:
            state = self.execution_states[task_id]
            state.execution_trace.status = "completed"
            state.execution_trace.end_time = datetime.utcnow()


class StateManager:
    """Manages system and execution state."""

    def __init__(self):
        """Initialize the state manager."""
        self.system_state = SystemState()
        self._execution_states: Dict[UUID, ExecutionState] = {}

    def get_system_state(self) -> SystemState:
        """Get current system state."""
        return self.system_state

    def get_execution_state(self, task_id: UUID) -> Optional[ExecutionState]:
        """Get execution state for a task."""
        return self._execution_states.get(task_id)

    def register_task(
        self, task_id: UUID, agent_id: str
    ) -> ExecutionState:
        """Register a new task."""
        state = ExecutionState(task_id=task_id, agent_id=agent_id)
        self._execution_states[task_id] = state
        self.system_state.active_tasks.append(task_id)
        return state

    def mark_task_complete(self, task_id: UUID, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark a task as complete."""
        if task_id in self._execution_states:
            state = self._execution_states[task_id]
            state.execution_trace.status = "completed"
            state.execution_trace.end_time = datetime.utcnow()
            state.execution_trace.final_result = result

    def get_active_tasks(self) -> List[UUID]:
        """Get list of active task IDs."""
        return self.system_state.active_tasks.copy()


# Global singleton
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create the global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def reset_state_manager() -> None:
    """Reset the global state manager."""
    global _state_manager
    _state_manager = None
