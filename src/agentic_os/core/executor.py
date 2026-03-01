"""
Executor Agent - Executes plans by invoking tools.

The executor agent receives execution plans and carries out
the individual steps, handling errors and retries.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from loguru import logger

from agentic_os.coordination.messages import (
    ExecutionPlan,
    ExecutionResult,
    Message,
    MessageType,
    TaskExecutionResult,
)
from agentic_os.core.agents import StatefulAgent
from agentic_os.core.state import get_state_manager
from agentic_os.core.telemetry import TelemetryManager
import time


class ExecutorAgent(StatefulAgent):
    """
    Agent responsible for executing plans.

    The executor:
    - Receives execution plans from planner
    - Invokes tools for each step
    - Handles tool results and errors
    - Manages retries on transient failures
    - Sends results to verifier
    """

    def __init__(self, agent_id: str = "executor"):
        """Initialize the executor agent."""
        super().__init__(agent_id, "executor")
        self.state_manager = get_state_manager()
        self.telemetry = TelemetryManager()

    async def execute_plan(self, plan: ExecutionPlan) -> TaskExecutionResult:
        """
        Execute a plan and return results (synchronous convenience method).
        Used by high-level interfaces like Discord bot.
        """
        start_time = time.time()
        step_results = []
        all_success = True

        logger.info(f"Executing plan {plan.id} with {len(plan.steps)} steps")

        for step in plan.steps:
            logger.debug(f"Executing step {step.order}: {step.description}")
            result = await self._execute_step(step)
            step_results.append(result)
            
            if not result.success:
                all_success = False
                logger.error(f"Step {step.id} failed: {result.error}")
                # We continue to other steps if they don't depend on this one, 
                # but for simplicity in synchronous execution we can choose to stop.
                # However, to match the agent behavior we should probably continue or handle dependencies.

        duration_ms = int((time.time() - start_time) * 1000)
        
        return TaskExecutionResult(
            task_id=plan.task_id,
            plan_id=plan.id,
            success=all_success,
            step_results=step_results,
            latency_ms=duration_ms,
            token_usage={"total": 0}  # Placeholder for now
        )

    async def _register_message_handlers(self) -> None:
        """Register handlers for execution requests."""
        if self._bus:
            await self._bus.subscribe(MessageType.EXECUTE_REQUEST, self.handle_message)
            logger.info("ExecutorAgent registered for EXECUTE_REQUEST messages")

    async def handle_message(self, message: Message) -> None:
        """
        Handle incoming plan responses.

        Args:
            message: Plan response message
        """
        self.state.messages_processed += 1
        start_time = time.time()

        try:
            # Extract plan from payload
            plan_data = message.payload.get("plan")
            task_id_str = message.payload.get("task_id")
            
            if not plan_data:
                logger.error("No plan in message")
                return

            if not task_id_str:
                logger.error("No task_id in message")
                return

            from uuid import UUID
            task_id = UUID(task_id_str)
            
            # Reconstruct ExecutionPlan
            plan = ExecutionPlan(**plan_data)
            
            logger.info(f"Executing plan {plan.id} with {len(plan.steps)} steps")

            # Register task execution
            exec_state = self.state_manager.register_task(task_id, self.agent_id)
            exec_state.execution_trace.status = "running"

            # Execute each step
            results: Dict[UUID, ExecutionResult] = {}
            for step in plan.steps:
                logger.debug(f"Executing step {step.order}: {step.description}")

                # Check if dependencies are met
                if step.depends_on:
                    unmet = [dep for dep in step.depends_on if dep not in results]
                    if unmet:
                        logger.warning(f"Step {step.id} waiting on dependencies")
                        continue

                # Execute the tool
                result = await self._execute_step(step)
                results[step.id] = result
                
                # Log Telemetry for tool call
                self.telemetry.log_tool_call(str(task_id), step.tool_name, result.success)

                # Store in trace
                exec_state.execution_trace.steps_executed.append({
                    "step_id": str(step.id),
                    "order": step.order,
                    "description": step.description,
                    "success": result.success,
                    "duration_ms": result.duration_ms,
                })

                if not result.success:
                    logger.error(f"Step {step.id} failed: {result.error}")
                    # Could implement retry logic here
                    exec_state.execution_trace.errors.append({
                        "step_id": str(step.id),
                        "error": result.error,
                    })

            # Log overall task latency
            duration_ms = (time.time() - start_time) * 1000
            self.telemetry.log_task_latency(str(task_id), "executor", duration_ms)

            # Mark task as complete
            self.state_manager.mark_task_complete(task_id, {
                "plan_id": str(plan.id),
                "results": {str(k): v.model_dump() for k, v in results.items()},
            })

            # Send to verifier
            await self._send_message(
                recipient="verifier",
                message_type=MessageType.VERIFY_REQUEST,
                payload={
                    "plan_id": str(plan.id),
                    "task_id": str(task_id),
                    "results": {str(k): v.model_dump() for k, v in results.items()},
                    "execution_trace": exec_state.execution_trace.model_dump(),
                },
                correlation_id=message.id,
                parent_message_id=message.id,
            )
            
            logger.info(f"Plan {plan.id} execution complete")

        except Exception as e:
            logger.error(f"Error in executor: {e}")
            self.state.errors_encountered += 1

    async def _execute_step(self, step) -> ExecutionResult:  # type: ignore[no-untyped-def]
        """
        Execute a single plan step.

        Args:
            step: Plan step to execute

        Returns:
            Execution result
        """
        from datetime import datetime, timezone
        import time

        start_time = time.time()

        try:
            # Get the tool
            tool = self._registry.get(step.tool_name)
            if not tool:
                error_msg = f"Tool '{step.tool_name}' not found"
                logger.error(error_msg)
                return ExecutionResult(
                    step_id=step.id,
                    success=False,
                    error=error_msg,
                    duration_ms=int((time.time() - start_time) * 1000),
                    timestamp=datetime.now(timezone.utc),
                )

            # Execute the tool
            logger.debug(f"Calling tool: {step.tool_name} with args: {step.tool_args}")
            try:
                output = await tool.validate_and_execute(**step.tool_args)
            except Exception as tool_error:
                logger.error(f"Tool execution failed: {tool_error}")
                duration_ms = int((time.time() - start_time) * 1000)
                return ExecutionResult(
                    step_id=step.id,
                    success=False,
                    error=str(tool_error),
                    duration_ms=duration_ms,
                    timestamp=datetime.now(timezone.utc),
                )

            duration_ms = int((time.time() - start_time) * 1000)

            error_msg = output.error if hasattr(output, 'error') and output.error else None
            
            return ExecutionResult(
                step_id=step.id,
                success=output.success,
                output=output.data if hasattr(output, 'data') else output,
                error=error_msg,
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Tool execution failed: {e}")
            return ExecutionResult(
                step_id=step.id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                timestamp=datetime.now(timezone.utc),
            )
