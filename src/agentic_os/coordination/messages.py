"""
Message definitions for inter-agent communication.

This module defines the message schema and contracts used by the coordination
bus for agent-to-agent communication.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of messages in the system."""

    # Task orchestration
    PLAN_REQUEST = "plan_request"
    PLAN_RESPONSE = "plan_response"
    EXECUTE_REQUEST = "execute_request"
    EXECUTE_RESPONSE = "execute_response"
    VERIFY_REQUEST = "verify_request"
    VERIFY_RESPONSE = "verify_response"

    # Tool invocation
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"

    # Status and control
    AGENT_READY = "agent_ready"
    AGENT_BUSY = "agent_busy"
    CANCEL_REQUEST = "cancel_request"
    HEARTBEAT = "heartbeat"

    # Data exchange
    CONTEXT_UPDATE = "context_update"
    STATE_SYNC = "state_sync"

    # Error handling
    REQUEST_FAILED = "request_failed"
    RECOVERABLE_ERROR = "recoverable_error"
    CRITICAL_ERROR = "critical_error"


class MessageStatus(str, Enum):
    """Status of message processing."""

    SENT = "sent"
    DELIVERED = "delivered"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class Message(BaseModel):
    """
    Base message class for agent communication.

    Each message has:
    - Unique ID for tracking and correlation
    - Type for routing and handling
    - Sender and recipient identification
    - Payload with actual data
    - Timestamps for observability
    - Status tracking for reliability
    """

    id: UUID = Field(default_factory=uuid4, description="Unique message identifier")
    message_type: MessageType = Field(description="Type of message")
    sender: str = Field(description="Agent ID of sender")
    recipient: str = Field(description="Agent ID of recipient (or 'broadcast')")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message content")
    status: MessageStatus = Field(default=MessageStatus.SENT, description="Current status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    sent_at: Optional[datetime] = Field(default=None, description="When message was sent")
    delivered_at: Optional[datetime] = Field(default=None, description="When message was delivered")
    completed_at: Optional[datetime] = Field(default=None, description="When processing completed")
    correlation_id: Optional[UUID] = Field(
        default=None, description="ID to correlate request/response pairs"
    )
    parent_message_id: Optional[UUID] = Field(
        default=None, description="ID of message that triggered this one"
    )
    error: Optional[str] = Field(default=None, description="Error message if status is FAILED")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional contextual data"
    )


class TaskDefinition(BaseModel):
    """Definition of a task to be planned and executed."""

    id: UUID = Field(default_factory=uuid4, description="Task identifier")
    user_request: str = Field(description="Natural language user request")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Contextual information for task"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Constraints on execution (timeout, tools allowed, etc)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PlanStep(BaseModel):
    """A single step in an execution plan."""

    id: UUID = Field(default_factory=uuid4)
    order: int = Field(description="Execution order")
    description: str = Field(description="Human-readable description of step")
    tool_name: str = Field(description="Tool to invoke for this step")
    tool_args: Dict[str, Any] = Field(description="Arguments for the tool")
    depends_on: List[UUID] = Field(
        default_factory=list, description="IDs of steps that must complete first"
    )
    expected_output_schema: Optional[Dict[str, Any]] = Field(
        default=None, description="Expected output structure for verification"
    )


class ExecutionPlan(BaseModel):
    """Complete plan for executing a task."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID = Field(description="ID of task being planned")
    steps: List[PlanStep] = Field(description="Steps in execution order")
    reasoning: str = Field(description="Why this plan was generated")
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence in plan success"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(description="Agent that created the plan")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional plan metadata")


class ExecutionResult(BaseModel):
    """Result of executing a single step."""

    step_id: UUID = Field(description="ID of executed step")
    success: bool = Field(description="Whether execution succeeded")
    output: Any = Field(default=None, description="Tool output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration_ms: int = Field(description="Time taken in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VerificationResult(BaseModel):
    """Result of verifying plan execution."""

    plan_id: UUID = Field(description="ID of executed plan")
    task_id: UUID = Field(description="ID of original task")
    verified: bool = Field(description="Whether execution meets requirements")
    issues: List[str] = Field(default_factory=list, description="Any discrepancies found")
    recommendations: List[str] = Field(
        default_factory=list, description="Suggestions for correction if verification failed"
    )
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_by: str = Field(description="Agent that performed verification")
