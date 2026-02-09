"""
Reminders tool for scheduling and managing reminders.

Time-based reminder scheduling with persistence.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from agentic_os.config import get_settings
from agentic_os.tools.base import Tool, ToolInput, ToolOutput


class ReminderSetInput(ToolInput):
    """Input for setting a reminder."""

    message: str = Field(description="Reminder message")
    time: str = Field(
        description="When to remind (e.g., '2h', '3pm', '2025-02-09 15:30', 'tomorrow 10am')"
    )
    priority: str = Field(
        default="normal", description="Priority: high, normal, low"
    )


class ReminderSetOutput(ToolOutput):
    """Output from setting a reminder."""

    reminder_id: str = Field(description="Unique reminder ID")
    scheduled_time: str = Field(description="Scheduled time (ISO format)")
    time_until: str = Field(description="Time until reminder (e.g., '2h 30m')")


class ReminderSetTool(Tool):
    """Tool for setting reminders."""

    def __init__(self):
        """Initialize the reminder set tool."""
        super().__init__(
            name="reminder_set",
            description="Set a reminder for a specific time",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return ReminderSetInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return ReminderSetOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        Set a reminder.

        Args:
            **kwargs: Arguments matching ReminderSetInput

        Returns:
            ReminderSetOutput with reminder details
        """
        message = kwargs.get("message", "").strip()
        time_str = kwargs.get("time", "").strip()
        priority = kwargs.get("priority", "normal").lower()

        if not message or not time_str:
            return ReminderSetOutput(
                success=False,
                error="Message and time are required",
                reminder_id="",
                scheduled_time="",
                time_until="",
            )

        try:
            # Parse time input
            now = datetime.now(timezone.utc)
            scheduled_time = self._parse_time(time_str, now)

            if scheduled_time <= now:
                return ReminderSetOutput(
                    success=False,
                    error="Reminder time must be in the future",
                    reminder_id="",
                    scheduled_time="",
                    time_until="",
                )

            # Generate reminder ID
            reminder_id = f"rem-{now.timestamp()}"

            # Store reminder
            settings = get_settings()
            reminders_file = settings.data_dir / "reminders.json"

            reminders = []
            if reminders_file.exists():
                reminders = json.loads(reminders_file.read_text())

            reminders.append(
                {
                    "id": reminder_id,
                    "message": message,
                    "scheduled_time": scheduled_time.isoformat(),
                    "priority": priority,
                    "created_at": now.isoformat(),
                    "is_active": True,
                }
            )

            reminders_file.write_text(json.dumps(reminders, indent=2))

            # Calculate time until
            time_until = self._format_time_delta(scheduled_time - now)

            return ReminderSetOutput(
                success=True,
                reminder_id=reminder_id,
                scheduled_time=scheduled_time.isoformat(),
                time_until=time_until,
                data={
                    "reminder_id": reminder_id,
                    "message": message,
                    "scheduled_time": scheduled_time.isoformat(),
                    "priority": priority,
                    "time_until": time_until,
                },
            )

        except Exception as e:
            return ReminderSetOutput(
                success=False,
                error=f"Reminder setting failed: {str(e)}",
                reminder_id="",
                scheduled_time="",
                time_until="",
            )

    @staticmethod
    def _parse_time(time_str: str, base_time: datetime) -> datetime:
        """Parse various time formats."""
        time_str = time_str.lower().strip()

        # Relative formats: "2h", "30m", "tomorrow", "next monday"
        if time_str.endswith("h"):
            hours = int(time_str[:-1])
            return base_time + timedelta(hours=hours)
        elif time_str.endswith("m"):
            minutes = int(time_str[:-1])
            return base_time + timedelta(minutes=minutes)
        elif time_str == "tomorrow":
            return base_time + timedelta(days=1)
        elif time_str.startswith("tomorrow"):
            # "tomorrow 3pm"
            parts = time_str.split()
            if len(parts) > 1:
                time_part = parts[-1]
                hour = int(time_part.replace("pm", "").replace("am", ""))
                if "pm" in time_part and hour != 12:
                    hour += 12
                return (base_time + timedelta(days=1)).replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
        elif ":" in time_str or time_str.endswith(("am", "pm")):
            # Today at specific time: "3pm", "15:30"
            if time_str.endswith("pm"):
                hour = int(time_str.replace("pm", "").strip())
                if hour != 12:
                    hour += 12
            elif time_str.endswith("am"):
                hour = int(time_str.replace("am", "").strip())
                if hour == 12:
                    hour = 0
            else:
                hour = int(time_str.split(":")[0])
            return base_time.replace(hour=hour, minute=0, second=0, microsecond=0)

        # Default: treat as ISO string
        return datetime.fromisoformat(time_str)

    @staticmethod
    def _format_time_delta(delta: timedelta) -> str:
        """Format timedelta as readable string."""
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class ReminderListInput(ToolInput):
    """Input for listing reminders."""

    filter_status: str = Field(
        default="active", description="Filter: 'active', 'completed', 'all'"
    )


class ReminderListOutput(ToolOutput):
    """Output from listing reminders."""

    reminders: list[dict] = Field(default_factory=list, description="List of reminders")
    total_count: int = Field(default=0, description="Total reminders")


class ReminderListTool(Tool):
    """Tool for listing reminders."""

    def __init__(self):
        """Initialize the reminder list tool."""
        super().__init__(
            name="reminder_list",
            description="List all active reminders",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return ReminderListInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return ReminderListOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        List reminders.

        Args:
            **kwargs: Arguments matching ReminderListInput

        Returns:
            ReminderListOutput with reminder list
        """
        filter_status = kwargs.get("filter_status", "active").lower()

        try:
            settings = get_settings()
            reminders_file = settings.data_dir / "reminders.json"

            if not reminders_file.exists():
                return ReminderListOutput(
                    success=True, reminders=[], total_count=0
                )

            all_reminders = json.loads(reminders_file.read_text())
            now = datetime.now(timezone.utc)

            # Filter based on status
            reminders = []
            for reminder in all_reminders:
                scheduled = datetime.fromisoformat(reminder["scheduled_time"])
                is_passed = scheduled <= now

                if filter_status == "active" and reminder["is_active"] and not is_passed:
                    reminders.append(reminder)
                elif filter_status == "completed" and (not reminder["is_active"] or is_passed):
                    reminders.append(reminder)
                elif filter_status == "all":
                    reminders.append(reminder)

            # Sort by scheduled time
            reminders.sort(
                key=lambda r: r["scheduled_time"]
            )

            return ReminderListOutput(
                success=True,
                reminders=reminders,
                total_count=len(reminders),
                data={"reminders": reminders},
            )

        except Exception as e:
            return ReminderListOutput(
                success=False,
                error=f"Reminder listing failed: {str(e)}",
            )
