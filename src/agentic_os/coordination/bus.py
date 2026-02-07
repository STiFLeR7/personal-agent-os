"""
Message bus for coordinating agent communication.

This module implements a centralized message broker that routes messages
between agents, ensures delivery, and maintains message history for
observability and debugging.
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger

from agentic_os.coordination.messages import Message, MessageStatus, MessageType


class MessageBus:
    """
    Centralized message bus for agent communication.

    Features:
    - Message routing and delivery guarantees
    - Subscriber management for message types
    - Message history for observability
    - Automatic timeout handling
    - Correlation tracking for request/response pairs
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize the message bus.

        Args:
            max_history: Maximum number of messages to retain in history
        """
        self.max_history = max_history
        self._message_history: List[Message] = []
        self._subscribers: Dict[str, Set[Callable[[Message], None]]] = defaultdict(set)
        self._pending_responses: Dict[UUID, asyncio.Future[Message]] = {}
        self._lock = asyncio.Lock()

    async def publish(self, message: Message) -> None:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish
        """
        async with self._lock:
            message.sent_at = datetime.now(timezone.utc)
            message.status = MessageStatus.SENT

            # Store in history
            self._message_history.append(message)
            if len(self._message_history) > self.max_history:
                self._message_history.pop(0)

            logger.debug(
                f"Message published: {message.message_type} from {message.sender} to {message.recipient}"
            )

        # Route to any waiting handlers
        await self._route_message(message)

    async def subscribe(
        self, message_type: MessageType, handler: Callable[[Message], None]
    ) -> None:
        """
        Subscribe to messages of a specific type.

        Args:
            message_type: Type of messages to subscribe to
            handler: Async callable to handle messages
        """
        self._subscribers[message_type.value].add(handler)
        logger.debug(f"Handler subscribed to {message_type.value}")

    async def unsubscribe(
        self, message_type: MessageType, handler: Callable[[Message], None]
    ) -> None:
        """
        Unsubscribe a handler from messages.

        Args:
            message_type: Type of messages to unsubscribe from
            handler: Handler to remove
        """
        self._subscribers[message_type.value].discard(handler)
        logger.debug(f"Handler unsubscribed from {message_type.value}")

    async def _route_message(self, message: Message) -> None:
        """
        Route a message to all relevant subscribers.

        Args:
            message: Message to route
        """
        # Get handlers for this message type
        handlers = self._subscribers.get(message.message_type.value, set())

        # Route to broadcast subscribers if needed
        if message.recipient == "broadcast":
            handlers.update(self._subscribers.get("broadcast", set()))

        # Call each handler
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

        # If this was a response to a pending request, resolve the future
        if message.correlation_id and message.correlation_id in self._pending_responses:
            future = self._pending_responses.pop(message.correlation_id)
            if not future.done():
                future.set_result(message)
                message.status = MessageStatus.COMPLETED
                message.completed_at = datetime.now(timezone.utc)

    async def request_response(
        self, message: Message, timeout_seconds: int = 30
    ) -> Message:
        """
        Send a message and wait for a response (request-response pattern).

        Args:
            message: Message to send
            timeout_seconds: How long to wait for response

        Returns:
            Response message

        Raises:
            asyncio.TimeoutError: If no response received within timeout
        """
        # Set up correlation for response tracking
        message.correlation_id = message.id
        future: asyncio.Future[Message] = asyncio.Future()
        self._pending_responses[message.correlation_id] = future

        try:
            # Publish the request
            await self.publish(message)

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout_seconds)
            return response
        except asyncio.TimeoutError:
            logger.error(f"No response to message {message.id} within {timeout_seconds}s")
            message.status = MessageStatus.TIMEOUT
            message.completed_at = datetime.now(timezone.utc)
            self._pending_responses.pop(message.correlation_id, None)
            raise

    def get_history(
        self,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100,
    ) -> List[Message]:
        """
        Retrieve message history with optional filtering.

        Args:
            sender: Filter by sender agent ID
            recipient: Filter by recipient agent ID
            message_type: Filter by message type
            limit: Maximum number of messages to return

        Returns:
            List of messages matching criteria
        """
        results = []
        for msg in reversed(self._message_history):
            if sender and msg.sender != sender:
                continue
            if recipient and msg.recipient != recipient:
                continue
            if message_type and msg.message_type != message_type:
                continue

            results.append(msg)
            if len(results) >= limit:
                break

        return list(reversed(results))

    def clear_history(self) -> int:
        """Clear message history and return count of cleared messages."""
        count = len(self._message_history)
        self._message_history.clear()
        self._pending_responses.clear()
        logger.info(f"Cleared {count} messages from history")
        return count

    async def shutdown(self) -> None:
        """Gracefully shut down the bus."""
        logger.info("Shutting down message bus")
        self._subscribers.clear()

        # Fail any pending requests
        for future in self._pending_responses.values():
            if not future.done():
                future.set_exception(RuntimeError("Bus is shutting down"))

        self._pending_responses.clear()


# Global singleton bus instance
_bus: Optional[MessageBus] = None


async def get_bus() -> MessageBus:
    """Get or create the global message bus instance."""
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


async def reset_bus() -> None:
    """Reset the global bus (useful for testing)."""
    global _bus
    if _bus:
        await _bus.shutdown()
    _bus = None
