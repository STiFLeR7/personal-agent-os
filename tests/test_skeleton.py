"""
Skeleton test file for basic system validation.
"""

import pytest


class TestImports:
    """Test that core modules can be imported."""

    def test_import_config(self) -> None:
        """Test config module imports."""
        from agentic_os.config import get_settings, Settings
        
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_import_coordination(self) -> None:
        """Test coordination modules import."""
        from agentic_os.coordination import Message, MessageType, MessageBus
        
        assert MessageType.PLAN_REQUEST

    def test_import_core(self) -> None:
        """Test core modules import."""
        from agentic_os.core import Agent, AgentState, PlanningEngine
        
        assert Agent
        assert AgentState
        assert PlanningEngine

    def test_import_tools(self) -> None:
        """Test tools modules import."""
        from agentic_os.tools import Tool, ToolRegistry, get_tool_registry
        
        registry = get_tool_registry()
        assert isinstance(registry, ToolRegistry)


class TestConfiguration:
    """Test configuration system."""

    def test_default_settings(self) -> None:
        """Test default settings load correctly."""
        from agentic_os.config import Settings, reset_settings
        
        reset_settings()
        settings = Settings()
        
        assert settings.llm.provider == "ollama"
        assert settings.agent.planning_depth > 0
        assert settings.data_dir.exists()

    def test_settings_singleton(self) -> None:
        """Test settings singleton pattern."""
        from agentic_os.config import get_settings, reset_settings
        
        reset_settings()
        s1 = get_settings()
        s2 = get_settings()
        
        assert s1 is s2


@pytest.mark.asyncio
async def test_message_bus() -> None:
    """Test message bus functionality."""
    from agentic_os.coordination import Message, MessageType, MessageBus, reset_bus
    
    await reset_bus()
    bus = MessageBus()
    
    msg = Message(
        message_type=MessageType.AGENT_READY,
        sender="test_agent",
        recipient="test_recipient",
        payload={"status": "ready"},
    )
    
    await bus.publish(msg)
    history = bus.get_history(sender="test_agent")
    
    assert len(history) == 1
    assert history[0].sender == "test_agent"


def test_state_manager() -> None:
    """Test state management."""
    from agentic_os.core import get_state_manager, reset_state_manager
    from uuid import uuid4
    
    reset_state_manager()
    manager = get_state_manager()
    
    task_id = uuid4()
    state = manager.register_task(task_id, "test_agent")
    
    assert state.task_id == task_id
    assert task_id in manager.get_active_tasks()


def test_planning_validator() -> None:
    """Test plan validation."""
    from agentic_os.core.planning import PlanValidator
    from agentic_os.coordination.messages import ExecutionPlan, PlanStep
    from uuid import uuid4
    
    # Valid plan
    steps = [
        PlanStep(
            id=uuid4(),
            order=1,
            description="Step 1",
            tool_name="test_tool",
            tool_args={},
        )
    ]
    
    plan = ExecutionPlan(
        id=uuid4(),
        task_id=uuid4(),
        steps=steps,
        reasoning="Test plan",
        created_by="test",
    )
    
    validator = PlanValidator(plan=plan)
    assert validator.validate() is True
