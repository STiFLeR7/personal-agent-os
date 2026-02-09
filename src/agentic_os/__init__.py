"""
Dex: Your Personal AI Operator.

Dex is a production-grade personal AI operator that handles your tasks through
planning, execution, and verification. Designed for local-first, privacy-focused
autonomous task management with voice integration ready.

"Hey Dex!" - Voice activation name
"""

__version__ = "0.2.0"  # Phase 3: Advanced Tools & Voice Ready
__author__ = "Personal AI Systems"
__agent_name__ = "Dex"

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
