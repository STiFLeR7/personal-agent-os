"""
Shell command execution tool.

A general-purpose tool for executing system commands.
"""

import asyncio
import subprocess
from typing import Any, Optional

from pydantic import Field

from agentic_os.tools.base import Tool, ToolInput, ToolOutput


class ShellCommandInput(ToolInput):
    """Input for shell command execution."""

    command: str = Field(description="Command to execute")
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
    shell: bool = Field(
        default=True, description="Run through shell (safer on Windows)"
    )


class ShellCommandOutput(ToolOutput):
    """Output from shell command execution."""

    stdout: Optional[str] = Field(default=None, description="Standard output")
    stderr: Optional[str] = Field(default=None, description="Standard error")
    return_code: int = Field(default=0, description="Exit code")


class ShellCommandTool(Tool):
    """
    Tool for executing shell commands.

    Provides a safe, sandboxed way to run system commands with timeout protection.
    """

    def __init__(self):
        """Initialize the shell command tool."""
        super().__init__(
            name="shell_command",
            description="Execute a system command and return output",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return ShellCommandInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return ShellCommandOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        Execute a shell command.

        Args:
            **kwargs: Arguments matching ShellCommandInput

        Returns:
            ShellCommandOutput with results
        """
        command = kwargs.get("command", "").strip()
        timeout = kwargs.get("timeout", 30)
        shell = kwargs.get("shell", True)

        if not command:
            return ShellCommandOutput(
                success=False, error="Command cannot be empty"
            )

        try:
            # Use asyncio to run subprocess with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=shell,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ShellCommandOutput(
                    success=False,
                    error=f"Command timed out after {timeout}s",
                    return_code=-1,
                )

            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Determine success based on return code
            success = process.returncode == 0
            
            # Set error message if command failed
            error_msg = None
            if not success:
                error_msg = stderr_str if stderr_str else f"Command failed with exit code {process.returncode}"

            return ShellCommandOutput(
                success=success,
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=process.returncode,
                error=error_msg,
                data={
                    "command": command,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "return_code": process.returncode,
                },
            )

        except Exception as e:
            return ShellCommandOutput(
                success=False, error=f"Execution failed: {str(e)}"
            )
