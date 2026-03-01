"""Tool integration layer."""

from agentic_os.tools.base import (
    Tool,
    ToolInput,
    ToolOutput,
    ToolRegistry,
    get_tool_registry,
    reset_tool_registry,
)
from agentic_os.tools.shell_command import ShellCommandTool
from agentic_os.tools.file_operations import FileReadTool, FileWriteTool
from agentic_os.tools.notes import NoteCreateTool, NoteListTool
from agentic_os.tools.reminders import ReminderSetTool, ReminderListTool
from agentic_os.tools.email_browser import EmailComposeTool, BrowserOpenTool
from agentic_os.tools.app_tools import AppLaunchTool
from agentic_os.tools.chat import GenericChatTool
from agentic_os.tools.time_utils import (
    get_current_time,
    parse_relative_time,
    format_time_since,
    format_time_until,
    is_business_hours,
    get_greeting,
)

__all__ = [
    # Base classes
    "Tool",
    "ToolInput",
    "ToolOutput",
    "ToolRegistry",
    "get_tool_registry",
    "reset_tool_registry",
    # Tools
    "ShellCommandTool",
    "FileReadTool",
    "FileWriteTool",
    "NoteCreateTool",
    "NoteListTool",
    "ReminderSetTool",
    "ReminderListTool",
    "EmailComposeTool",
    "BrowserOpenTool",
    "AppLaunchTool",
    "GenericChatTool",
    # Time utilities
    "get_current_time",
    "parse_relative_time",
    "format_time_since",
    "format_time_until",
    "is_business_hours",
    "get_greeting",
]
