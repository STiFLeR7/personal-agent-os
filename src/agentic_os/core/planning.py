"""
Planning and reasoning engine.

This module implements the core planning logic that decomposes user requests
into executable steps, validates plans, and supports replanning on failures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field

from agentic_os.coordination.messages import ExecutionPlan, PlanStep, TaskDefinition


class PlanningContext(BaseModel):
    """Context used during planning."""

    task: TaskDefinition = Field(description="Task being planned")
    available_tools: List[str] = Field(
        description="Tool names available for planning"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict, description="Execution constraints"
    )
    prior_attempts: List[Dict[str, Any]] = Field(
        default_factory=list, description="Previous plan attempts (for replanning)"
    )


class PlanValidator(BaseModel):
    """Validates execution plans for soundness."""

    plan: ExecutionPlan = Field(description="Plan to validate")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Warnings")

    def validate(self) -> bool:
        """
        Validate the plan.

        Returns:
            True if plan is valid, False otherwise
        """
        self.errors.clear()
        self.warnings.clear()

        # Check for empty plan
        if not self.plan.steps:
            self.errors.append("Plan has no execution steps")
            return False

        # Check for circular dependencies
        if self._has_circular_dependency():
            self.errors.append("Plan has circular step dependencies")
            return False

        # Check for undefined dependencies
        step_ids = {step.id for step in self.plan.steps}
        for step in self.plan.steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    self.errors.append(
                        f"Step {step.id} depends on undefined step {dep_id}"
                    )

        # Check step ordering respects dependencies
        if not self._check_ordering():
            self.warnings.append(
                "Step ordering may not respect all dependencies"
            )

        return len(self.errors) == 0

    def _has_circular_dependency(self) -> bool:
        """Check for circular dependencies in the plan."""
        visited: set[UUID] = set()
        rec_stack: set[UUID] = set()

        def dfs(step_id: UUID) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)

            step = next((s for s in self.plan.steps if s.id == step_id), None)
            if not step:
                return False

            for dep_id in step.depends_on:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(step_id)
            return False

        for step in self.plan.steps:
            if step.id not in visited:
                if dfs(step.id):
                    return True

        return False

    def _check_ordering(self) -> bool:
        """Check that step ordering respects dependencies."""
        step_positions = {step.id: i for i, step in enumerate(self.plan.steps)}

        for step in self.plan.steps:
            for dep_id in step.depends_on:
                if dep_id in step_positions:
                    if step_positions[dep_id] >= step_positions[step.id]:
                        return False

        return True


class PlanningEngine:
    """
    Core reasoning engine for planning task execution.

    This is an interface that LLM-based planning logic will implement.
    Currently provides validation and common planning utilities.
    """

    def __init__(self):
        """Initialize the planning engine."""
        self.validator = PlanValidator(plan=ExecutionPlan(
            id=UUID(int=0),
            task_id=UUID(int=0),
            steps=[],
            reasoning="",
            created_by="engine"
        ))

    async def plan_task(
        self,
        task: TaskDefinition,
        available_tools: List[str],
        max_depth: int = 5,
    ) -> Optional[ExecutionPlan]:
        """
        Generate an execution plan for a task.

        Args:
            task: Task to plan
            available_tools: Tools available for the plan
            max_depth: Maximum planning depth

        Returns:
            Execution plan or None if planning fails
        """
        logger.info(f"Planning task: {task.user_request}")

        context = PlanningContext(
            task=task,
            available_tools=available_tools,
            constraints=task.constraints,
        )

        # TODO: Implement actual LLM-based planning
        # For now, return None to indicate planning not yet implemented
        logger.warning("Planning engine not yet implemented - returning None")
        return None

    async def validate_plan(self, plan: ExecutionPlan) -> bool:
        """
        Validate an execution plan.

        Args:
            plan: Plan to validate

        Returns:
            True if valid, False otherwise
        """
        self.validator.plan = plan
        is_valid = self.validator.validate()

        if not is_valid:
            logger.error(f"Plan validation failed: {self.validator.errors}")
        if self.validator.warnings:
            logger.warning(f"Plan warnings: {self.validator.warnings}")

        return is_valid

    async def replan_on_failure(
        self,
        original_plan: ExecutionPlan,
        original_task: TaskDefinition,
        failure_reason: str,
        available_tools: List[str],
    ) -> Optional[ExecutionPlan]:
        """
        Generate a revised plan after execution failure.

        Args:
            original_plan: Plan that failed
            original_task: Original task
            failure_reason: Why the plan failed
            available_tools: Available tools

        Returns:
            Revised plan or None if replanning fails
        """
        logger.warning(
            f"Replanning after failure: {failure_reason}"
        )

        # Add context about the failure for replanning
        context = PlanningContext(
            task=original_task,
            available_tools=available_tools,
            constraints=original_task.constraints,
            prior_attempts=[
                {
                    "plan_id": str(original_plan.id),
                    "failure_reason": failure_reason,
                    "steps": [step.model_dump() for step in original_plan.steps],
                }
            ],
        )

        # TODO: Implement actual LLM-based replanning
        logger.warning("Replanning engine not yet implemented - returning None")
        return None

    def decompose_goal_into_steps(
        self,
        goal: str,
        available_tools: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Decompose a goal into logical steps.

        This is a utility for planning that can be overridden by subclasses.

        Args:
            goal: Goal to decompose
            available_tools: Available tools

        Returns:
            List of step descriptions
        """
        # Simple placeholder - to be replaced by LLM-based decomposition
        return [
            {
                "order": 1,
                "description": f"Process: {goal}",
                "tool": available_tools[0] if available_tools else "unknown",
            }
        ]

    def estimate_task_complexity(self, task: TaskDefinition) -> float:
        """
        Estimate task complexity (0.0 = trivial, 1.0 = maximum).

        Args:
            task: Task to estimate

        Returns:
            Complexity score
        """
        # Count words as proxy for complexity
        word_count = len(task.user_request.split())
        return min(1.0, word_count / 100.0)
