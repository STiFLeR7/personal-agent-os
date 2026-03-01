"""
Base classes and interfaces for tool integration.

This module defines the tool abstraction layer, allowing tools to be plugged in
without coupling tool-specific logic to agent reasoning. All tools follow a
uniform schema: name, description, input schema, and sync/async execution.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


class ToolInput(BaseModel):
    """Base class for tool input validation."""

    model_config = ConfigDict(
        extra="ignore", # Be permissive with LLM hallucinations
        populate_by_name=True
    )


class ToolOutput(BaseModel):
    """Base class for tool output."""

    success: bool = Field(description="Whether the tool execution succeeded")
    data: Optional[Any] = Field(default=None, description="Tool output data")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class Tool(ABC):
    """
    Abstract base class for all tools.

    Tools are self-describing units of functionality that agents can invoke.
    Each tool must define:
    - Metadata (name, description)
    - Input schema (Pydantic model for validation)
    - Execution logic (sync or async)
    - Output schema
    """

    def __init__(self, name: str, description: str):
        """
        Initialize a tool.

        Args:
            name: Unique identifier for the tool (e.g., 'send_email', 'read_file')
            description: Human-readable description
        """
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def input_schema(self) -> type[ToolInput]:
        """Return the Pydantic model class for validating inputs."""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> type[ToolOutput]:
        """Return the Pydantic model class for output."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        Execute the tool.

        Args:
            **kwargs: Arguments matching the input_schema

        Returns:
            ToolOutput with success/data/error fields
        """
        pass

    async def validate_and_execute(self, **kwargs: Any) -> ToolOutput:
        """
        Validate inputs and execute the tool.

        This method handles input validation, error handling, and logging.

        Args:
            **kwargs: Raw arguments to validate and pass to execute()

        Returns:
            ToolOutput with results or error information
        """
        try:
            # Validate inputs
            input_obj = self.input_schema(**kwargs)
            logger.debug(f"Tool '{self.name}' called with validated input")

            # Execute
            result = await self.execute(**input_obj.model_dump())

            # Validate output
            output = self.output_schema(**result.model_dump())
            logger.debug(
                f"Tool '{self.name}' executed: success={output.success}"
            )
            return output

        except ValueError as e:
            logger.error(f"Invalid input for tool '{self.name}': {e}")
            return self.output_schema(
                success=False, error=f"Invalid input: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Execution error in tool '{self.name}': {e}")
            return self.output_schema(
                success=False, error=f"Execution failed: {str(e)}"
            )

    def __str__(self) -> str:
        """String representation of the tool."""
        return f"Tool(name='{self.name}', description='{self.description}')"

    def to_schema_dict(self) -> Dict[str, Any]:
        """
        Export tool metadata as a schema dictionary for agent consumption.

        Returns:
            Dictionary with tool name, description, and input schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.model_json_schema(),
        }


class ToolRegistry:
    """
    Registry for managing all available tools.

    The registry allows agents to discover and invoke tools without knowing
    their implementation details.
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with this name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.debug(f"Tool '{tool.name}' registered")

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return dict(self._tools)

    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get schemas for all tools (for agent consumption).

        Returns:
            Dictionary mapping tool names to their schemas
        """
        return {name: tool.to_schema_dict() for name, tool in self._tools.items()}

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if tool was registered and removed
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Tool '{name}' unregistered")
            return True
        return False


# Global singleton registry
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def reset_tool_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _registry
    _registry = None
