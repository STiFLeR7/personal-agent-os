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
        Generate a plan using Gemini.
        """
        if not self.model:
            logger.error("Gemini model not initialized. Check LLM_API_KEY and LLM_PROVIDER.")
            return None

        # Fetch relevant context from memory
        context_entries = self.memory_engine.search_semantic(task.user_request, limit=3)
        context_text = "\n".join([f"- {m.content}" for m in context_entries])
        session_context = self.memory_engine.get_all_session_context()

        prompt = self._build_planning_prompt(task, available_tools, context_text, session_context)
        
        try:
            response = await self.model.generate_content_async(prompt)
            raw_output = json.loads(response.text)
            
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
                created_by="gemini-planner"
            )

            # Evaluate Risk
            risk_score = self.risk_engine.evaluate_plan([s.model_dump() for s in steps])
            plan.metadata["risk_score"] = risk_score.model_dump()
            
            logger.info(f"Gemini generated plan with {len(steps)} steps. Risk: {risk_score.level}")
            
            return plan

        except Exception as e:
            logger.error(f"Gemini planning failed: {e}")
            return None

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
