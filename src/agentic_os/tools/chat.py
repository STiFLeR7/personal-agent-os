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

        # Helper for Groq Fallback
        async def _try_groq(reason: str):
            if not self.settings.llm.groq_api_key:
                return ChatOutput(success=False, error=f"Gemini failed ({reason}) and Groq not configured.", response="")

            logger.info(f"Gemini failed ({reason}), falling back to Groq...")
            import aiohttp
            headers = {
                "Authorization": f"Bearer {self.settings.llm.groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": query}],
                "temperature": 0.7
            }

            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data["choices"][0]["message"]["content"].strip()
                        return ChatOutput(success=True, response=response_text, data={"response": response_text})
                    else:
                        err_text = await resp.text()
                        return ChatOutput(success=False, error=f"Groq fallback failed: {err_text}", response="")

        try:
            # 1. Try Gemini
            if self.settings.llm.provider == "google" and self.settings.llm.api_key:
                import google.generativeai as genai
                genai.configure(api_key=self.settings.llm.api_key)
                model = genai.GenerativeModel(self.settings.llm.model_name or "gemini-2.0-flash")
                try:
                    response = await model.generate_content_async(query)
                    return ChatOutput(success=True, response=response.text, data={"response": response.text})
                except Exception as e:
                    return await _try_groq(str(e))

            # 2. Try Groq (if preferred or Gemini not configured)
            elif self.settings.llm.groq_api_key:
                return await _try_groq("Gemini not configured")

            # 3. No LLM configured
            return ChatOutput(
                success=True, 
                response="I am a local agent. LLM provider is not fully configured, but I hear you!",
                data={"response": "LLM provider not configured. I hear you!"}
            )
        except Exception as e:
            logger.error(f"ChatTool failed: {e}")
            return ChatOutput(success=False, error=str(e), response="")

