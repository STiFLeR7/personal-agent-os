"""
Gemini-powered reasoning and planning engine.

This module implements structured task decomposition and tool selection using
Google's Gemini models with JSON-schema constrained output.
"""

import json
import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import google.generativeai as genai
from loguru import logger
from pydantic import BaseModel, Field

from agentic_os.config import get_settings
from agentic_os.coordination.messages import ExecutionPlan, PlanStep, TaskDefinition
from agentic_os.core.planning import PlanningEngine
from agentic_os.core.risk import RiskEngine, RiskScore
from agentic_os.core.memory import ContextMemoryEngine


class GeminiPlanOutput(BaseModel):
    """Schema for Gemini's structured planning response."""

    steps: List[Dict[str, Any]] = Field(description="List of plan steps with tool_name and tool_args")
    reasoning: str = Field(description="Explanation of the planning logic")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    risk_assessment: str = Field(description="Brief internal risk assessment")


class GeminiPlanner(PlanningEngine):
    """
    Advanced planner using Gemini for reasoning.
    """

    def __init__(self, risk_engine: Optional[RiskEngine] = None, memory_engine: Optional[ContextMemoryEngine] = None):
        """Initialize with Gemini API, Risk Engine, and Memory Engine."""
        super().__init__()
        self.settings = get_settings()
        self.risk_engine = risk_engine or RiskEngine()
        self.memory_engine = memory_engine or ContextMemoryEngine()
        
        if self.settings.llm.provider == "google" and self.settings.llm.api_key:
            genai.configure(api_key=self.settings.llm.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.settings.llm.model_name or "gemini-2.0-flash",
                generation_config={"response_mime_type": "application/json"}
            )
        else:
            self.model = None
            logger.warning("Gemini API not configured. GeminiPlanner will be unavailable.")

    async def plan_task(
        self,
        task: TaskDefinition,
        available_tools: List[str],
        max_depth: int = 5,
    ) -> Optional[ExecutionPlan]:
        """
        Generate a plan using Gemini with automatic Groq fallback.
        """
        # Fetch relevant context from memory
        context_entries = self.memory_engine.search_semantic(task.user_request, limit=3)
        context_text = "\n".join([f"- {m.content}" for m in context_entries])
        session_context = self.memory_engine.get_all_session_context()

        prompt = self._build_planning_prompt(task, available_tools, context_text, session_context)
        
        # Helper for Groq Fallback
        async def _try_groq_planning(reason: str):
            if not self.settings.llm.groq_api_key:
                logger.error(f"Gemini planning failed ({reason}) and Groq not configured.")
                return None
            
            logger.info(f"Gemini planning failed ({reason}), falling back to Groq...")
            import aiohttp
            headers = {
                "Authorization": f"Bearer {self.settings.llm.groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.1 # Low temperature for planning
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_output = json.loads(data["choices"][0]["message"]["content"])
                        return self._process_plan_output(raw_output, task)
                    else:
                        err_text = await resp.text()
                        logger.error(f"Groq planning fallback failed: {err_text}")
                        return None

        # 1. Try Gemini
        if self.model:
            try:
                response = await self.model.generate_content_async(prompt)
                raw_output = json.loads(response.text)
                return self._process_plan_output(raw_output, task)
            except Exception as e:
                return await _try_groq_planning(str(e))
        else:
            # 2. Try Groq directly if Gemini model not initialized
            return await _try_groq_planning("Gemini model not initialized")

    def _process_plan_output(self, raw_output: Dict[str, Any], task: TaskDefinition) -> ExecutionPlan:
        """Process raw JSON output into an ExecutionPlan object."""
        # Validate output against schema
        plan_data = GeminiPlanOutput(**raw_output)
        
        # Convert steps to PlanStep objects
        steps = []
        for i, step_data in enumerate(plan_data.steps):
            steps.append(PlanStep(
                id=uuid4(),
                order=i + 1,
                description=step_data.get("description", f"Step {i+1}"),
                tool_name=step_data["tool_name"],
                tool_args=step_data.get("tool_args", {}),
                depends_on=[] # Simple sequential for now
            )
        )

        # Create ExecutionPlan
        plan = ExecutionPlan(
            id=uuid4(),
            task_id=task.id,
            steps=steps,
            reasoning=plan_data.reasoning,
            confidence=plan_data.confidence,
            created_by="dual-core-planner"
        )

        # Evaluate Risk
        risk_score = self.risk_engine.evaluate_plan([s.model_dump() for s in steps])
        plan.metadata["risk_score"] = risk_score.model_dump()
        
        logger.info(f"Generated plan with {len(steps)} steps. Risk: {risk_score.level}")
        return plan

    def _build_planning_prompt(
        self, 
        task: TaskDefinition, 
        available_tools: List[str], 
        context: str = "",
        session: Dict[str, Any] = None
    ) -> str:
        """Construct the planning prompt for Gemini with memory context."""
        import sys
        os_name = sys.platform
        session_text = json.dumps(session or {}, indent=2)
        return f"""
        You are Dex, a high-performance personal AI operator. 
        Your goal is to decompose the user's request into a deterministic execution plan.
        
        SYSTEM ENVIRONMENT:
        - OS: {os_name}
        - Current Working Directory: {os.getcwd()}

        RELEVANT CONTEXT FROM MEMORY:
        {context if context else "No prior context found."}

        CURRENT SESSION STATE:
        {session_text}

        USER REQUEST: "{task.user_request}"
        AVAILABLE TOOLS: {available_tools}
        
        TASK RULES:
        1. Only use the tools provided in the list.
        2. Provide arguments that exactly match the tool's expected input schema.
        3. Be concise but thorough.
        4. Assess risk and confidence.

        RESPONSE FORMAT (JSON):
        {{
            "steps": [
                {{
                    "description": "Human readable description",
                    "tool_name": "tool_name",
                    "tool_args": {{ "arg1": "val1" }}
                }}
            ],
            "reasoning": "Why this approach was taken",
            "confidence": 0.95,
            "risk_assessment": "Internal notes on safety"
        }}
        """
