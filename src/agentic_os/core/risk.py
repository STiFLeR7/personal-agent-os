"""
Risk Engine - Evaluates security and operational risks of planned actions.

This module provides risk classification, permission gating, and human-in-the-loop
confirmation mechanisms for high-risk operations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Classification of execution risk."""

    LOW = "low"        # Read-only or idempotent local actions
    MEDIUM = "medium"  # File modifications, system changes
    HIGH = "high"      # Shell commands, destructive actions, network calls


class RiskScore(BaseModel):
    """Detailed risk assessment for a plan or step."""

    level: RiskLevel = Field(description="Overall risk level")
    score: float = Field(ge=0.0, le=1.0, description="Numerical risk score")
    reasoning: str = Field(description="Explanation for the risk assessment")
    mitigations: List[str] = Field(default_factory=list, description="Suggested mitigations")

    @property
    def risk_level(self) -> str:
        """Alias for level value used by some integrations."""
        return self.level.value


class RiskEngine:
    """
    Evaluates risks and enforces safety gates.
    """

    def __init__(self, mode: str = "balanced"):
        """
        Initialize the risk engine.

        Args:
            mode: Safety mode ('strict', 'balanced', 'permissive')
        """
        self.mode = mode

    def evaluate_step(self, tool_name: str, args: Dict[str, Any]) -> RiskScore:
        """
        Evaluate the risk of a single plan step.

        Args:
            tool_name: Name of the tool to be invoked
            args: Arguments for the tool

        Returns:
            Risk score for the step
        """
        # Hardcoded risk rules for baseline tools
        high_risk_tools = ["shell_command"]
        medium_risk_tools = ["file_write", "note_create", "reminder_set", "app_launch"]
        
        if tool_name in high_risk_tools:
            return RiskScore(
                level=RiskLevel.HIGH,
                score=0.9,
                reasoning=f"Tool '{tool_name}' allows arbitrary execution which is high risk.",
                mitigations=["User confirmation required", "Review command string"]
            )
        
        if tool_name in medium_risk_tools:
            return RiskScore(
                level=RiskLevel.MEDIUM,
                score=0.5,
                reasoning=f"Tool '{tool_name}' modifies local state or launches applications.",
                mitigations=["Check file paths", "Validate input content"]
            )
        
        return RiskScore(
            level=RiskLevel.LOW,
            score=0.1,
            reasoning=f"Tool '{tool_name}' is considered low risk.",
        )

    def evaluate_plan(self, steps: List[Dict[str, Any]]) -> RiskScore:
        """
        Evaluate the overall risk of an execution plan.

        Args:
            steps: List of plan steps

        Returns:
            Aggregate risk score
        """
        scores = [self.evaluate_step(s["tool_name"], s.get("tool_args", {})) for s in steps]
        
        if not scores:
            return RiskScore(level=RiskLevel.LOW, score=0.0, reasoning="Empty plan")

        max_score = max(s.score for s in scores)
        
        if max_score >= 0.8:
            level = RiskLevel.HIGH
        elif max_score >= 0.4:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskScore(
            level=level,
            score=max_score,
            reasoning=f"Aggregate risk based on {len(steps)} steps. Highest risk step is {level.value}."
        )

    def analyze_plan(self, plan: Any) -> RiskScore:
        """
        Analyze a plan and return a risk report. 
        Compatibility method for high-level callers like Discord.
        """
        from agentic_os.coordination.messages import ExecutionPlan
        
        if isinstance(plan, ExecutionPlan):
            steps = [s.model_dump() for s in plan.steps]
        elif isinstance(plan, list):
            steps = plan
        else:
            # Try to model_dump if it's a Pydantic model
            try:
                steps = plan.model_dump().get("steps", [])
            except Exception:
                steps = []

        return self.evaluate_plan(steps)

    def requires_confirmation(self, risk: RiskScore) -> bool:
        """
        Determine if a task requires human confirmation based on risk and mode.
        """
        if self.mode == "strict":
            return risk.level != RiskLevel.LOW
        if self.mode == "permissive":
            return risk.level == RiskLevel.HIGH and risk.score > 0.95
        
        # Balanced mode (default)
        return risk.level == RiskLevel.HIGH
