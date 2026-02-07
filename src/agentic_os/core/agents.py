"""
Core agent abstractions and base classes.

This module defines the Agent base class that all specialized agents
(Planner, Executor, Verifier) inherit from. Handles messaging, lifecycle,
state management, and common agentic patterns.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

from agentic_os.coordination.bus import MessageBus, get_bus
from agentic_os.coordination.messages import Message, MessageStatus, MessageType
from agentic_os.tools.base import ToolRegistry, get_tool_registry


class AgentState(BaseModel):
    """State information for an agent."""

    agent_id: str = Field(description="Unique agent identifier")
    agent_type: str = Field(description="Type of agent (e.g., 'planner', 'executor')")
    status: str = Field(default="idle", description="Current status (idle, busy, error)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages_processed: int = Field(default=0, description="Total messages handled")
    errors_encountered: int = Field(default=0, description="Total errors encountered")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom state data")


class Agent(ABC):
    """
    Base class for all agents in the system.

    Agents are autonomous entities that:
    - Receive and respond to messages
    - Maintain internal state and context
    - Collaborate with other agents via the message bus
    - Have distinct responsibilities (planning, execution, verification, etc)
    """

    def __init__(self, agent_id: str, agent_type: str):
        """
        Initialize an agent.

        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type/role of agent
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState(agent_id=agent_id, agent_type=agent_type)
        self._bus: Optional[MessageBus] = None
        self._registry = get_tool_registry()

    async def initialize(self, bus: Optional[MessageBus] = None) -> None:
        """
        Initialize the agent and connect to the message bus.

        Args:
            bus: Message bus instance (will use global bus if not provided)
        """
        self._bus = bus or await get_bus()
        logger.info(f"Agent '{self.agent_id}' initialized (type: {self.agent_type})")

        # Register handlers for this agent's message types
        await self._register_message_handlers()

        # Send ready notification
        await self._send_status_update("ready")

    async def shutdown(self) -> None:
        """Gracefully shut down the agent."""
        logger.info(f"Agent '{self.agent_id}' shutting down")
        await self._send_status_update("shutdown")

    @abstractmethod
    async def handle_message(self, message: Message) -> None:
        """
        Handle an incoming message.

        Subclasses must implement this to define their behavior.

        Args:
            message: Incoming message
        """
        pass

    @abstractmethod
    async def _register_message_handlers(self) -> None:
        """
        Register this agent's message handlers with the bus.

        Subclasses define which message types they handle.
        """
        pass

    async def _send_message(
        self,
        recipient: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        correlation_id: Optional[UUID] = None,
        parent_message_id: Optional[UUID] = None,
    ) -> Message:
        """
        Send a message to another agent.

        Args:
            recipient: ID of recipient agent
            message_type: Type of message
            payload: Message content
            correlation_id: For correlating request/response pairs
            parent_message_id: Reference to message that triggered this

        Returns:
            The sent message
        """
        message = Message(
            message_type=message_type,
            sender=self.agent_id,
            recipient=recipient,
            payload=payload,
            correlation_id=correlation_id,
            parent_message_id=parent_message_id,
        )

        if self._bus:
            await self._bus.publish(message)
        else:
            logger.warning(f"Agent '{self.agent_id}' not connected to bus")

        return message

    async def _send_broadcast(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
    ) -> Message:
        """
        Broadcast a message to all agents.

        Args:
            message_type: Type of message
            payload: Message content

        Returns:
            The sent message
        """
        return await self._send_message("broadcast", message_type, payload)

    async def _send_status_update(self, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Send a status update to interested agents.

        Args:
            status: Current status (e.g., 'ready', 'busy', 'error')
            details: Optional status details
        """
        self.state.status = status
        self.state.last_activity = datetime.now(timezone.utc)

        payload = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": status,
        }
        if details:
            payload.update(details)

        await self._send_broadcast(MessageType.AGENT_READY, payload)

    async def _acknowledge_message(self, original_message: Message) -> None:
        """
        Send an acknowledgment for a received message.

        Args:
            original_message: The message being acknowledged
        """
        self.state.messages_processed += 1

        if original_message.correlation_id:
            await self._send_message(
                original_message.sender,
                MessageType.AGENT_READY,
                {"acknowledged": True},
                correlation_id=original_message.correlation_id,
                parent_message_id=original_message.id,
            )

    def get_available_tools(self) -> List[str]:
        """Get list of tool names available to this agent."""
        return list(self._registry.list_tools().keys())

    def get_tool_schemas(self) -> Dict[str, Any]:
        """Get schemas for all available tools."""
        return self._registry.get_schemas()

    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log an event in the agent's execution trace.

        Args:
            event_type: Type of event (e.g., 'decision', 'tool_call', 'error')
            details: Event details
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **details,
        }

        if "events" not in self.state.metadata:
            self.state.metadata["events"] = []

        self.state.metadata["events"].append(entry)
        logger.debug(f"Event logged by {self.agent_id}: {event_type}")


class SynchronousAgent(Agent):
    """
    Agent variant for synchronous request-response interaction.

    Useful for agents that respond to specific message types synchronously.
    """

    async def _request_response(
        self,
        recipient: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        timeout_seconds: int = 30,
    ) -> Message:
        """
        Send a request and wait synchronously for a response.

        Args:
            recipient: Target agent
            message_type: Request type
            payload: Request payload
            timeout_seconds: Response timeout

        Returns:
            Response message

        Raises:
            RuntimeError: If not connected to bus
        """
        if not self._bus:
            raise RuntimeError(f"Agent '{self.agent_id}' not connected to bus")

        message = Message(
            message_type=message_type,
            sender=self.agent_id,
            recipient=recipient,
            payload=payload,
        )

        return await self._bus.request_response(message, timeout_seconds)


class StatefulAgent(Agent):
    """
    Agent variant with explicit state management.

    Useful for agents that maintain context across multiple interactions.
    """

    def __init__(self, agent_id: str, agent_type: str):
        """Initialize with state tracking."""
        super().__init__(agent_id, agent_type)
        self.context: Dict[str, Any] = {}

    def update_context(self, key: str, value: Any) -> None:
        """Update agent context."""
        self.context[key] = value
        logger.debug(f"Agent '{self.agent_id}' context updated: {key}")

    def clear_context(self) -> None:
        """Clear all context."""
        self.context.clear()
        logger.debug(f"Agent '{self.agent_id}' context cleared")

    def get_context(self, key: str, default: Any = None) -> Any:
        """Retrieve a context value."""
        return self.context.get(key, default)
