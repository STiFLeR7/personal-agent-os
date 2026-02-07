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
        # Check for file/directory listing operations
        if any(word in request for word in ["list", "files", "directory", "dir", "show files", "share file", "file names", "files in"]):
            return await self._plan_list_files(task)

        # Check for browser/application opening (must check before generic "open")
        elif any(word in request for word in ["chrome", "firefox", "browser", "edge", "explorer"]):
            return await self._plan_open_application(task)

        # Check for settings/preferences (more specific)
        elif any(word in request for word in ["settings", "preferences", "config"]):
            return await self._plan_open_settings(task)

        # Check for email operations
        elif any(
            word in request for word in ["write", "send", "email", "message"]
        ):
            return await self._plan_send_email(task)

        # Check for file reading (must come after list operations)
        elif any(word in request for word in ["read", "show", "display", "content"]) and "file" in request:
            return await self._plan_read_file(task)

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

    async def _plan_send_email(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to send an email."""
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
            ),
            PlanStep(
                id=uuid4(),
                order=2,
                description="Send email",
                tool_name="email_send",
                tool_args={},
                depends_on=[steps[0].id] if steps else [],
            ),
        ]

        return ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning="User requested to send an email. Plan includes composing and sending.",
            confidence=0.85,
            created_by=self.agent_id,
        )

    async def _plan_read_file(self, task: TaskDefinition) -> ExecutionPlan:
        """Create a plan to read a file."""
        file_path = task.context.get("file_path", "")

        # Use type command on Windows, cat on Unix
        import sys
        if sys.platform == "win32":
            command = f"type {file_path}"
        else:
            command = f"cat {file_path}"

        steps = [
            PlanStep(
                id=uuid4(),
                order=1,
                description=f"Read file: {file_path}",
                tool_name="shell_command",
                tool_args={"command": command},
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
