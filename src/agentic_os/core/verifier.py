"""
Verifier Agent - Validates execution results.

The verifier agent checks that execution outcomes match expectations
and determines if the task was completed successfully.
"""

from datetime import datetime, timezone
from typing import Dict, Any
from uuid import UUID

from loguru import logger

from agentic_os.coordination.messages import (
    Message,
    MessageType,
    VerificationResult,
)
from agentic_os.core.agents import StatefulAgent


class VerifierAgent(StatefulAgent):
    """
    Agent responsible for verifying execution results.

    The verifier:
    - Receives execution results from executor
    - Validates outcomes against expectations
    - Checks for errors and inconsistencies
    - Provides feedback on task completion
    """

    def __init__(self, agent_id: str = "verifier"):
        """Initialize the verifier agent."""
        super().__init__(agent_id, "verifier")

    async def _register_message_handlers(self) -> None:
        """Register handlers for verification requests."""
        if self._bus:
            await self._bus.subscribe(MessageType.VERIFY_REQUEST, self.handle_message)
            logger.info("VerifierAgent registered for VERIFY_REQUEST messages")

    async def handle_message(self, message: Message) -> None:
        """
        Handle incoming verification requests.

        Args:
            message: Verification request message
        """
        self.state.messages_processed += 1

        try:
            # Extract data from payload
            plan_id = message.payload.get("plan_id")
            task_id = message.payload.get("task_id")
            results = message.payload.get("results", {})
            execution_trace = message.payload.get("execution_trace", {})

            if not all([plan_id, task_id]):
                logger.error("Missing plan_id or task_id in verification request")
                return

            logger.info(f"Verifying execution of task {task_id}")

            # Perform verification
            verification = await self._verify_execution(
                plan_id, task_id, results, execution_trace
            )

            # Log verification result
            if verification.verified:
                logger.info(f"✓ Task {task_id} verified successfully")
            else:
                logger.warning(f"✗ Task {task_id} verification failed: {verification.issues}")

            # Broadcast verification result
            await self._send_broadcast(
                MessageType.VERIFY_RESPONSE,
                {
                    "plan_id": plan_id,
                    "task_id": task_id,
                    "verified": verification.verified,
                    "issues": verification.issues,
                    "recommendations": verification.recommendations,
                },
            )

        except Exception as e:
            logger.error(f"Error in verifier: {e}")
            self.state.errors_encountered += 1

    async def _verify_execution(
        self,
        plan_id: str,
        task_id: str,
        results: Dict[str, Any],
        execution_trace: Dict[str, Any],
    ) -> VerificationResult:
        """
        Verify an execution.

        Args:
            plan_id: ID of executed plan
            task_id: ID of task
            results: Results from each step
            execution_trace: Execution trace information

        Returns:
            Verification result
        """
        from uuid import UUID

        issues: list[str] = []
        recommendations: list[str] = []

        # Check if all steps executed
        steps_executed = execution_trace.get("steps_executed", [])
        if not steps_executed:
            issues.append("No steps were executed")
            recommendations.append("Review the execution plan for issues")

        # Check for errors
        errors = execution_trace.get("errors", [])
        if errors:
            issues.append(f"Execution encountered {len(errors)} error(s)")
            for error in errors:
                issues.append(f"  - Step {error.get('step_id')}: {error.get('error')}")
            recommendations.append("Review errors and retry failed steps")

        # Check result success
        all_successful = all(
            step.get("success", False) for step in steps_executed
        )

        # Determine overall verification
        verified = len(issues) == 0 and all_successful

        return VerificationResult(
            plan_id=UUID(plan_id),
            task_id=UUID(task_id),
            verified=verified,
            issues=issues,
            recommendations=recommendations,
            verified_by=self.agent_id,
        )
