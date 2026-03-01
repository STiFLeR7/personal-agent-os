"""
Chat tool for handling conversational or generic LLM queries.
"""

from typing import Any

from pydantic import Field
from loguru import logger

from agentic_os.config import get_settings
from agentic_os.tools.base import Tool, ToolInput, ToolOutput


from pydantic import Field, AliasChoices

class ChatInput(ToolInput):
    """Input for generic chat queries."""
    query: str = Field(
        description="The user's query or conversational prompt.",
        validation_alias=AliasChoices("query", "prompt", "text")
    )


class ChatOutput(ToolOutput):
    """Output from the chat query."""
    response: str = Field(default="", description="The LLM's response to the query.")


class GenericChatTool(Tool):
    """Tool for generic conversational responses."""

    def __init__(self):
        super().__init__(
            name="generic_chat",
            description="Use this for conversational queries, jokes, or general questions.",
        )
        self.settings = get_settings()

    @property
    def input_schema(self) -> type[ToolInput]:
        return ChatInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        return ChatOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        query = kwargs.get("query", "").strip()
        if not query:
            return ChatOutput(success=False, error="Query cannot be empty", response="")

        try:
            if self.settings.llm.provider == "google" and self.settings.llm.api_key:
                import google.generativeai as genai
                genai.configure(api_key=self.settings.llm.api_key)
                model = genai.GenerativeModel(self.settings.llm.model_name or "gemini-2.0-flash")
                response = await model.generate_content_async(query)
                return ChatOutput(success=True, response=response.text, data={"response": response.text})
            else:
                return ChatOutput(
                    success=True, 
                    response="I am a local agent. LLM provider is not fully configured, but I hear you!",
                    data={"response": "LLM provider not configured. I hear you!"}
                )
        except Exception as e:
            logger.error(f"ChatTool failed: {e}")
            return ChatOutput(success=False, error=str(e), response="")
