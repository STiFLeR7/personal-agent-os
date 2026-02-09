"""
Notes tool for persistent note-taking.

Store and retrieve notes with timestamps.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from agentic_os.config import get_settings
from agentic_os.tools.base import Tool, ToolInput, ToolOutput


class NoteCreateInput(ToolInput):
    """Input for creating a note."""

    title: str = Field(description="Note title")
    content: str = Field(description="Note content")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags")


class NoteCreateOutput(ToolOutput):
    """Output from note creation."""

    note_id: str = Field(description="Unique note ID")
    file_path: str = Field(description="Path where note was stored")
    created_at: str = Field(description="Creation timestamp")


class NoteCreateTool(Tool):
    """Tool for creating and saving notes."""

    def __init__(self):
        """Initialize the note create tool."""
        super().__init__(
            name="note_create",
            description="Create and save a note",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return NoteCreateInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return NoteCreateOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        Create a note.

        Args:
            **kwargs: Arguments matching NoteCreateInput

        Returns:
            NoteCreateOutput with note details
        """
        title = kwargs.get("title", "Untitled").strip()
        content = kwargs.get("content", "").strip()
        tags = kwargs.get("tags", "")

        if not title or not content:
            return NoteCreateOutput(
                success=False,
                error="Title and content are required",
                note_id="",
                file_path="",
                created_at="",
            )

        try:
            settings = get_settings()
            notes_dir = settings.data_dir / "notes"
            notes_dir.mkdir(parents=True, exist_ok=True)

            # Generate note ID from timestamp
            now = datetime.now(timezone.utc)
            timestamp = now.isoformat().replace(":", "-").replace(".", "-")
            note_id = f"{timestamp[:19]}-{title[:20]}".lower().replace(" ", "-")
            note_file = notes_dir / f"{note_id}.md"

            # Format with metadata
            metadata = f"""---
title: {title}
created: {now.isoformat()}
tags: {tags if tags else 'untagged'}
---

{content}
"""

            note_file.write_text(metadata, encoding="utf-8")

            return NoteCreateOutput(
                success=True,
                note_id=note_id,
                file_path=str(note_file.absolute()),
                created_at=now.isoformat(),
                data={
                    "note_id": note_id,
                    "title": title,
                    "file_path": str(note_file.absolute()),
                    "created_at": now.isoformat(),
                },
            )

        except Exception as e:
            return NoteCreateOutput(
                success=False,
                error=f"Note creation failed: {str(e)}",
                note_id="",
                file_path="",
                created_at="",
            )


class NoteListInput(ToolInput):
    """Input for listing notes."""

    search_term: Optional[str] = Field(default=None, description="Search term or tag")


class NoteListOutput(ToolOutput):
    """Output from note listing."""

    notes: list[dict] = Field(default_factory=list, description="List of notes")
    total_count: int = Field(default=0, description="Total notes found")


class NoteListTool(Tool):
    """Tool for listing and searching notes."""

    def __init__(self):
        """Initialize the note list tool."""
        super().__init__(
            name="note_list",
            description="List and search notes",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return NoteListInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return NoteListOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """
        List notes.

        Args:
            **kwargs: Arguments matching NoteListInput

        Returns:
            NoteListOutput with list of notes
        """
        search_term = (kwargs.get("search_term", "") or "").lower()

        try:
            settings = get_settings()
            notes_dir = settings.data_dir / "notes"

            if not notes_dir.exists():
                return NoteListOutput(
                    success=True, notes=[], total_count=0, data={"notes": []}
                )

            notes = []
            for note_file in sorted(notes_dir.glob("*.md"), reverse=True):
                content = note_file.read_text(encoding="utf-8")

                # Simple search in content and filename
                if search_term and search_term not in content.lower():
                    continue

                notes.append(
                    {
                        "id": note_file.stem,
                        "filename": note_file.name,
                        "size_bytes": note_file.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            note_file.stat().st_mtime
                        ).isoformat(),
                    }
                )

            return NoteListOutput(
                success=True,
                notes=notes,
                total_count=len(notes),
                data={"notes": notes, "search_term": search_term},
            )

        except Exception as e:
            return NoteListOutput(
                success=False,
                error=f"Note listing failed: {str(e)}",
            )
