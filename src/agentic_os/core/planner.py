"""
Planner Agent - Decomposes tasks into executable plans.

The planner agent receives task requests and generates execution plans
that detail what steps need to be taken and in what order.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from loguru import logger

from agentic_os.coordination.messages import (
    ExecutionPlan,
    Message,
    MessageType,
    PlanStep,
    TaskDefinition,
)
from agentic_os.core.agents import StatefulAgent
from agentic_os.core.planning import PlanningEngine


class PlannerAgent(StatefulAgent):
    """
    Agent responsible for planning task execution.

    The planner:
    - Receives task requests
    - Decomposes them into concrete steps
    - Generates execution plans with reasoning
    - Validates plans before sending them to executor
    """

    def __init__(self, agent_id: str = "planner"):
        """Initialize the planner agent."""
        super().__init__(agent_id, "planner")
        self.planning_engine = PlanningEngine()

    async def _register_message_handlers(self) -> None:
        """Register handlers for plan requests."""
        if self._bus:
            await self._bus.subscribe(MessageType.PLAN_REQUEST, self.handle_message)
            logger.info("PlannerAgent registered for PLAN_REQUEST messages")

    async def handle_message(self, message: Message) -> None:
        """
        Handle incoming plan requests.

        Args:
            message: Plan request message
        """
        self.state.messages_processed += 1
        
        try:
            # Extract task from payload
            task_data = message.payload.get("task")
            if not task_data:
                await self._send_error_response(message, "No task in request")
                return

            # Parse task definition
            task = TaskDefinition(**task_data)
            logger.info(f"Planning task: {task.user_request}")

            # Get available tools
            available_tools = self.get_available_tools()
            self.update_context("available_tools", available_tools)

            # Generate plan
            plan = await self._generate_plan(task, available_tools)

            if plan:
                # Validate plan
                is_valid = await self.planning_engine.validate_plan(plan)
                if not is_valid:
                    logger.warning("Generated plan failed validation")

                # Send plan to executor
                await self._send_message(
                    recipient="executor",
                    message_type=MessageType.PLAN_RESPONSE,
                    payload={
                        "plan": plan.model_dump(),
                        "task_id": str(task.id),
                    },
                    correlation_id=message.id,
                    parent_message_id=message.id,
                )
                logger.info(f"Plan generated with {len(plan.steps)} steps")
            else:
                await self._send_error_response(
                    message, "Failed to generate plan"
                )

        except Exception as e:
            logger.error(f"Error in planner: {e}")
            await self._send_error_response(message, str(e))

    async def _generate_plan(
        self, task: TaskDefinition, available_tools: list[str]
    ) -> Optional[ExecutionPlan]:
        """
        Generate an execution plan for a task.

        Args:
            task: Task to plan
            available_tools: Available tools

        Returns:
            Execution plan or None if planning fails
        """
        # Simple rule-based planning for common tasks
        request = task.user_request.lower().strip()

        # Rule-based task routing - check more specific patterns first
        # Notes operations
        if any(word in request for word in ["note", "notes", "save", "remember"]):
            if any(word in request for word in ["list", "show", "all"]):
                return await self._plan_list_notes(task)
            else:
                return await self._plan_take_note(task)

        # Reminders and scheduling
        elif any(word in request for word in ["remind", "reminder", "alarm", "schedule"]):
            if any(word in request for word in ["list", "show", "all"]):
                return await self._plan_list_reminders(task)
            else:
                return await self._plan_set_reminder(task)

        # File operations
        elif any(word in request for word in ["read", "show", "display", "content", "view"]) and ("file" in request or "." in request):
            return await self._plan_read_file(task)

        elif any(word in request for word in ["write", "save", "create", "edit"]) and ("file" in request or ".txt" in request):
            return await self._plan_write_file(task)

        # File/directory listing operations
        elif any(word in request for word in ["list", "files", "directory", "dir", "show files", "share file", "file names", "files in"]):
            return await self._plan_list_files(task)

        # Browser/application opening (must check before generic "open")
        elif any(word in request for word in ["chrome", "firefox", "browser", "edge", "explorer", "navigate", "website", "url", "http"]):
            return await self._plan_open_application(task)

        # Settings/preferences (more specific)
        elif any(word in request for word in ["settings", "preferences", "config"]):
            return await self._plan_open_settings(task)

        # Email operations (stubs for now)
        elif any(
            word in request for word in ["write", "send", "email", "message", "gmail"]
        ):
            return self._plan_send_email_stub(task)

        else:
            # Fallback: create a simple generic task
            logger.warning(f"Unknown task type, creating generic plan: {request}")
            return self._plan_generic_task(task)

    async def _plan_open_application(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to open a browser or application."""
        request = task.user_request.lower()
        
        # Map application names to commands
        import sys
        if sys.platform == "win32":
            # Windows commands
            app_commands = {
                "chrome": "start chrome",
                "firefox": "start firefox",
                "edge": "start msedge",
                "explorer": "start explorer",
            }
        else:
            # Unix/Linux commands
            app_commands = {
                "chrome": "google-chrome",
                "firefox": "firefox",
                "edge": "microsoft-edge",
                "explorer": "nautilus",
            }
        
        # Find which app to open
        app_name = "chrome"  # default
        command = "start chrome"  # default
        
        for app, cmd in app_commands.items():
            if app in request:
                app_name = app
                command = cmd
                break
        
        # Check if user wants to perform actions like "choose third profile"
        action = ""
        if "profile" in request:
            action = " (profile selection needed)"
        if "new tab" in request or "new window" in request:
            if sys.platform == "win32":
                command += " --new-window"
            else:
                command += " --new-window"
        
        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description=f"Open {app_name}{action}",
                tool_name="shell_command",
                tool_args={"command": command},
            )
        ]
        
        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning=f"User requested to open {app_name}. Using shell command to launch application.",
            confidence=0.9,
            created_by=self.agent_id,
        )

    async def _plan_open_settings(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to open system settings."""
        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description="Open system settings",
                tool_name="shell_command",
                tool_args={"command": "start ms-settings:"},
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning="User requested to open settings. Using shell command to launch settings application.",
            confidence=0.95,
            created_by=self.agent_id,
        )

    async def _plan_list_files(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to list files."""
        request = task.user_request
        directory = task.context.get("directory", ".")
        
        # Try to extract directory path from the request using regex
        import re
        
        # Match patterns like "D:/dex/", "/path/to/dir", "C:\Users\..." etc
        path_pattern = r'[A-Za-z]:[\\/][^\s]*|/[\S]*'
        match = re.search(path_pattern, request)
        if match:
            directory = match.group(0).strip()
            logger.debug(f"Extracted directory from request: {directory}")

        # Use dir command on Windows, ls on Unix
        import sys
        if sys.platform == "win32":
            command = f"dir /B {directory}"
        else:
            command = f"ls -la {directory}"

        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description=f"List files in {directory}",
                tool_name="shell_command",
                tool_args={"command": command},
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning=f"User requested to list files in {directory}.",
            confidence=0.9,
            created_by=self.agent_id,
        )

    def _plan_generic_task(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a generic fallback plan."""
        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description=f"Execute: {task.user_request}",
                tool_name="generic_command",
                tool_args={"command": task.user_request},
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning=f"Generic plan for: {task.user_request}",
            confidence=0.5,
            created_by=self.agent_id,
        )

    async def _plan_take_note(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to take a note."""
        request = task.user_request
        # Simple extraction: "note: [title] - [content]"
        title = task.context.get("title", "Note")
        content = task.context.get("content", request)

        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description="Save note",
                tool_name="note_create",
                tool_args={
                    "title": title,
                    "content": content,
                    "tags": task.context.get("tags", ""),
                },
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning="User wants to save a note.",
            confidence=0.85,
            created_by=self.agent_id,
        )

    async def _plan_list_notes(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to list notes."""
        search_term = task.context.get("search_term", "")

        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description="List notes",
                tool_name="note_list",
                tool_args={"search_term": search_term},
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning="User wants to see their notes.",
            confidence=0.9,
            created_by=self.agent_id,
        )

    async def _plan_set_reminder(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to set a reminder."""
        message = task.context.get("message", task.user_request)
        time = task.context.get("time", "1h")  # Default to 1 hour
        priority = task.context.get("priority", "normal")

        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description=f"Set reminder: {message}",
                tool_name="reminder_set",
                tool_args={
                    "message": message,
                    "time": time,
                    "priority": priority,
                },
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning="User wants to set a reminder.",
            confidence=0.85,
            created_by=self.agent_id,
        )

    async def _plan_list_reminders(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to list reminders."""
        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description="List reminders",
                tool_name="reminder_list",
                tool_args={"filter_status": "active"},
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning="User wants to see active reminders.",
            confidence=0.9,
            created_by=self.agent_id,
        )

    async def _plan_write_file(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to write to a file."""
        file_path = task.context.get("file_path", "notes.txt")
        content = task.context.get("content", task.user_request)

        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description=f"Write to file: {file_path}",
                tool_name="file_write",
                tool_args={
                    "file_path": file_path,
                    "content": content,
                    "create_parents": True,
                },
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning=f"User wants to write content to {file_path}.",
            confidence=0.88,
            created_by=self.agent_id,
        )

    async def _plan_read_file(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to read a file."""
        file_path = task.context.get("file_path", "")

        # Extract file path from request if not in context
        if not file_path:
            import re
            # Match file paths and filenames (including extensions)
            # Priority: absolute paths, then filenames with extensions, then words
            patterns = [
                r'[A-Za-z]:[\\/][^\s]*',  # Windows absolute paths
                r'/[\S]*',                 # Unix absolute paths  
                r'\./[\S]*',               # Relative paths with ./
                r'[\w\-\.]+\.\w{2,}',      # Files with extensions (README.md, file.txt)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, task.user_request)
                if match:
                    file_path = match.group(0).strip()
                    logger.debug(f"Extracted file path from request: {file_path}")
                    break

        # Default if nothing found
        if not file_path:
            file_path = "."

        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description=f"Read file: {file_path}",
                tool_name="file_read",
                tool_args={"file_path": file_path, "encoding": "utf-8"},
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning=f"User requested to read {file_path}.",
            confidence=0.9,
            created_by=self.agent_id,
        )

    def _plan_send_email_stub(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a stub plan for email (to be implemented in v0.3)."""
        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description="Compose email",
                tool_name="email_compose",
                tool_args={
                    "recipient": task.context.get("recipient", ""),
                    "subject": task.context.get("subject", ""),
                    "body": task.context.get("body", task.user_request),
                },
            )
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning="Gmail integration coming in v0.3",
            confidence=0.5,
            created_by=self.agent_id,
        )

    async def _send_error_response(self, request_message: Message, error: str) -> None:
        """
        Send an error response.

        Args:
            request_message: Original request message
            error: Error message
        """
        await self._send_message(
            recipient=request_message.sender,
            message_type=MessageType.REQUEST_FAILED,
            payload={"error": error, "task_id": request_message.payload.get("task", {}).get("id")},
            correlation_id=request_message.id,
            parent_message_id=request_message.id,
        )
