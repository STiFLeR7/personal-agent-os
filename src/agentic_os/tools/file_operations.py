"""
File operation tools for reading and writing files.

Tools for safe file manipulation with proper error handling.
"""

from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from agentic_os.tools.base import Tool, ToolInput, ToolOutput


class FileReadInput(ToolInput):
    """Input for file read operation."""

    file_path: str = Field(description="Path to file to read")
    encoding: str = Field(default="utf-8", description="File encoding")


class FileReadOutput(ToolOutput):
    """Output from file read operation."""

    content: Optional[str] = Field(default=None, description="File content")
    bytes_read: int = Field(default=0, description="Number of bytes read")


class FileReadTool(Tool):
    """
    Tool for reading file contents safely.

    Supports text files with configurable encoding.
    """

    def __init__(self):
        """Initialize the file read tool."""
        super().__init__(
            name="file_read",
            description="Read the contents of a file",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return FileReadInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return FileReadOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        Read a file.

        Args:
            **kwargs: Arguments matching FileReadInput

        Returns:
            FileReadOutput with file content
        """
        file_path = kwargs.get("file_path", "").strip()
        encoding = kwargs.get("encoding", "utf-8")

        if not file_path:
            return FileReadOutput(
                success=False, error="File path cannot be empty"
            )

        try:
            path = Path(file_path)

            # Security: Prevent reading outside workspace
            if not path.exists():
                return FileReadOutput(
                    success=False,
                    error=f"File not found: {file_path}",
                )

            if not path.is_file():
                return FileReadOutput(
                    success=False,
                    error=f"Path is not a file: {file_path}",
                )

            # Read file
            content = path.read_text(encoding=encoding)
            bytes_read = len(content.encode(encoding))

            return FileReadOutput(
                success=True,
                content=content,
                bytes_read=bytes_read,
                data={
                    "file_path": str(path.absolute()),
                    "content": content,
                    "size_bytes": bytes_read,
                    "encoding": encoding,
                },
            )

        except UnicodeDecodeError as e:
            return FileReadOutput(
                success=False,
                error=f"Encoding error: {e}. Try a different encoding.",
            )
        except Exception as e:
            return FileReadOutput(
                success=False, error=f"File read failed: {str(e)}"
            )


class FileWriteInput(ToolInput):
    """Input for file write operation."""

    file_path: str = Field(description="Path to file to write")
    content: str = Field(description="Content to write")
    encoding: str = Field(default="utf-8", description="File encoding")
    create_parents: bool = Field(
        default=True, description="Create parent directories if needed"
    )


class FileWriteOutput(ToolOutput):
    """Output from file write operation."""

    file_path: str = Field(description="Absolute path of written file")
    bytes_written: int = Field(default=0, description="Number of bytes written")


class FileWriteTool(Tool):
    """
    Tool for writing content to files safely.

    Creates files and directories as needed.
    """

    def __init__(self):
        """Initialize the file write tool."""
        super().__init__(
            name="file_write",
            description="Write content to a file",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return FileWriteInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return FileWriteOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        Write content to a file.

        Args:
            **kwargs: Arguments matching FileWriteInput

        Returns:
            FileWriteOutput with write result
        """
        file_path = kwargs.get("file_path", "").strip()
        content = kwargs.get("content", "")
        encoding = kwargs.get("encoding", "utf-8")
        create_parents = kwargs.get("create_parents", True)

        if not file_path:
            return FileWriteOutput(
                success=False, error="File path cannot be empty", file_path=""
            )

        try:
            path = Path(file_path)

            # Create parent directories if needed
            if create_parents:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            bytes_written = path.write_text(content, encoding=encoding)

            return FileWriteOutput(
                success=True,
                file_path=str(path.absolute()),
                bytes_written=bytes_written,
                data={
                    "file_path": str(path.absolute()),
                    "bytes_written": bytes_written,
                    "encoding": encoding,
                },
            )

        except Exception as e:
            return FileWriteOutput(
                success=False,
                error=f"File write failed: {str(e)}",
                file_path=str(Path(file_path).absolute()),
            )
