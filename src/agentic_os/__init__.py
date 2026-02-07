"""
Agentic OS: A production-grade personal AI operator.

This package provides the core framework for building autonomous agentic systems
that perform real-world tasks through planning, execution, and verification.
"""

__version__ = "0.1.0"
__author__ = "Personal AI Systems"

from agentic_os.config import Settings, get_settings, reset_settings
from agentic_os.core.agents import Agent, AgentState, SynchronousAgent, StatefulAgent
from agentic_os.coordination.bus import MessageBus, get_bus, reset_bus
from agentic_os.coordination.messages import (
    Message,
    MessageType,
    MessageStatus,
    TaskDefinition,
    ExecutionPlan,
    ExecutionResult,
    VerificationResult,
)
from agentic_os.tools.base import Tool, ToolInput, ToolOutput, ToolRegistry, get_tool_registry

__all__ = [
    # Version
    "__version__",
    # Config
    "Settings",
    "get_settings",
    "reset_settings",
    # Core agents
    "Agent",
    "AgentState",
    "SynchronousAgent",
    "StatefulAgent",
    # Coordination
    "MessageBus",
    "get_bus",
    "reset_bus",
    # Messages
    "Message",
    "MessageType",
    "MessageStatus",
    "TaskDefinition",
    "ExecutionPlan",
    "ExecutionResult",
    "VerificationResult",
    # Tools
    "Tool",
    "ToolInput",
    "ToolOutput",
    "ToolRegistry",
    "get_tool_registry",
]
