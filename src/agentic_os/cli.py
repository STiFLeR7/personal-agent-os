"""
Command-line interface for Dex - Your Personal AI Operator.

Dex helps you get things done through intelligent task planning and execution.
Try: "Hey Dex!" for voice activation support (coming soon!)
"""

import asyncio
from typing import Optional
from uuid import uuid4

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

from agentic_os import __agent_name__, __version__
from agentic_os.config import get_settings
from agentic_os.coordination import TaskDefinition, get_bus, reset_bus
from agentic_os.core import (
    ExecutorAgent,
    PlannerAgent,
    VerifierAgent,
    get_state_manager,
)
from agentic_os.coordination.messages import Message, MessageType
from agentic_os.tools.base import get_tool_registry
from agentic_os.tools import (
    ShellCommandTool,
    FileReadTool,
    FileWriteTool,
    NoteCreateTool,
    NoteListTool,
    ReminderSetTool,
    ReminderListTool,
    EmailComposeTool,
    BrowserOpenTool,
    AppLaunchTool,
)

console = Console()


@click.group()
@click.option(
    "--debug", is_flag=True, help="Enable debug logging"
)
@click.version_option(__version__, "--version", "-v", prog_name=__agent_name__)
def cli(debug: bool) -> None:
    """Dex - Your Personal AI Operator."""
    settings = get_settings()
    settings.debug_mode = debug

    # Configure logging
    logger.remove()
    
    # Set log level based on debug flag
    log_level = "DEBUG" if debug else "WARNING"
    
    logger.add(
        lambda msg: console.print(msg, end=""),
        format=settings.logging.format,
        level=log_level,
    )
    if settings.logging.file:
        logger.add(settings.logging.file, level=log_level)


@cli.command()
def status() -> None:
    """Show system status."""
    state_manager = get_state_manager()
    system_state = state_manager.get_system_state()

    table = Table(title="System Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Active Tasks", str(len(system_state.active_tasks)))
    table.add_row("Active Agents", str(len(system_state.agent_states)))
    table.add_row("Timestamp", system_state.timestamp.isoformat())

    console.print(table)

    if system_state.active_tasks:
        console.print("\n[bold]Active Tasks:[/bold]")
        for task_id in system_state.active_tasks:
            console.print(f"  • {task_id}")


@cli.command()
@click.argument("request", required=False)
def run(request: Optional[str]) -> None:
    """
    Run a task with the system.

    If no request is provided, enters interactive mode.
    """
    if not request:
        request = console.input("[bold cyan]Enter task:[/bold cyan] ")

    if not request.strip():
        console.print("[yellow]No task provided.[/yellow]")
        return

    console.print(f"[bold]Running:[/bold] {request}\n")

    # Run the async task execution
    try:
        asyncio.run(_execute_task(request))
    except KeyboardInterrupt:
        console.print("\n[yellow]Task cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


async def _execute_task(request: str) -> None:
    """
    Execute a task through the agent system.

    Args:
        request: User's task request
    """
    # Get or create message bus
    bus = await get_bus()

    # Register all tools
    registry = get_tool_registry()
    tools = [
        ShellCommandTool(),
        FileReadTool(),
        FileWriteTool(),
        NoteCreateTool(),
        NoteListTool(),
        ReminderSetTool(),
        ReminderListTool(),
        EmailComposeTool(),
        BrowserOpenTool(),
        AppLaunchTool(),
    ]
    
    for tool in tools:
        try:
            registry.register(tool)
        except ValueError:
            pass  # Already registered

    # Initialize agents
    planner = PlannerAgent()
    executor = ExecutorAgent()
    verifier = VerifierAgent()

    await planner.initialize(bus)
    await executor.initialize(bus)
    await verifier.initialize(bus)

    console.print("[cyan]Agents initialized[/cyan]")

    # Create task
    task = TaskDefinition(
        id=uuid4(),
        user_request=request,
        context={},
        constraints={"timeout": 300},
    )

    # Send plan request to planner
    plan_request = Message(
        message_type=MessageType.PLAN_REQUEST,
        sender="cli",
        recipient="planner",
        payload={"task": task.model_dump()},
    )

    await bus.publish(plan_request)
    console.print("[cyan]Plan request sent[/cyan]")

    # Wait for verification result
    try:
        # Give agents time to process
        await asyncio.sleep(2)

        # Check for results
        history = bus.get_history(sender="verifier", message_type=MessageType.VERIFY_RESPONSE)
        
        if history:
            last_result = history[-1]
            payload = last_result.payload
            
            console.print("\n[bold green]✓ TASK EXECUTION COMPLETE[/bold green]\n")
            
            # Display execution results with real data
            results = payload.get("results", {})
            if results:
                console.print("[bold cyan]═══ RESULTS ═══[/bold cyan]")
                for step_id, result in results.items():
                    if result.get("success"):
                        # Extract tool output data
                        output_data = result.get("output", {})
                        if isinstance(output_data, dict):
                            data = output_data.get("data", output_data)
                        else:
                            data = output_data
                        
                        # Display based on tool type (infer from fields)
                        if "reminder_id" in str(data):
                            console.print(f"\n[green]📌 Reminder Set[/green]")
                            console.print(f"   ID: {data.get('reminder_id', 'N/A')}")
                            console.print(f"   Scheduled: {data.get('scheduled_time', 'N/A')}")
                            console.print(f"   In: {data.get('time_until', 'N/A')}")
                        elif "note_id" in str(data):
                            console.print(f"\n[green]📝 Note Saved[/green]")
                            console.print(f"   ID: {data.get('note_id', 'N/A')}")
                            console.print(f"   File: {data.get('file_path', 'N/A')}")
                            console.print(f"   Created: {data.get('created_at', 'N/A')}")
                        elif "bytes_written" in str(data):
                            console.print(f"\n[green]📄 File Written[/green]")
                            console.print(f"   Path: {data.get('file_path', 'N/A')}")
                            console.print(f"   Bytes: {data.get('bytes_written', 'N/A')}")
                        elif "size_bytes" in str(data) or "content" in str(data):
                            console.print(f"\n[green]📖 File Read[/green]")
                            console.print(f"   Path: {data.get('file_path', 'N/A')}")
                            console.print(f"   Size: {data.get('size_bytes', 'N/A')} bytes")
                            if data.get("content"):
                                content = data.get("content", "")
                                # Show first 500 chars
                                preview = content[:500]
                                if len(content) > 500:
                                    preview += "\n[cyan]...(truncated)[/cyan]"
                                console.print(f"\n[cyan]{preview}[/cyan]")
                        elif "notes" in str(data):
                            console.print(f"\n[green]📚 Notes List[/green]")
                            notes_list = data.get("notes", [])
                            if notes_list:
                                console.print(f"   Found {len(notes_list)} notes:")
                                for note in notes_list[:10]:  # Show first 10
                                    console.print(f"     • {note.get('filename', 'Unknown')}")
                            else:
                                console.print("   No notes found")
                        elif "reminders" in str(data):
                            console.print(f"\n[green]📋 Reminders List[/green]")
                            reminders_list = data.get("reminders", [])
                            if reminders_list:
                                console.print(f"   Found {len(reminders_list)} reminders:")
                                for rem in reminders_list[:10]:  # Show first 10
                                    console.print(f"     • {rem.get('message', 'Unknown')} @ {rem.get('scheduled_time', 'N/A')}")
                            else:
                                console.print("   No active reminders")
                        elif "launched" in str(data):
                            console.print(f"\n[green]🚀 Application Launched[/green]")
                            console.print(f"   App: {data.get('app_name', 'Unknown')}")
                            console.print(f"   Status: {data.get('status', 'Launched')}")
            
            # Show verification status
            if payload.get("verified"):
                console.print("\n[green][✓ OK] Verification passed[/green]")
            else:
                console.print("\n[red][✗ ERROR] Verification failed[/red]")
                if payload.get("issues"):
                    console.print("[yellow]Issues:[/yellow]")
                    for issue in payload.get("issues", []):
                        console.print(f"  - {issue}")

            if payload.get("recommendations"):
                console.print("\n[cyan]Recommendations:[/cyan]")
                for rec in payload.get("recommendations", []):
                    console.print(f"  - {rec}")
        else:
            # No results yet - show what was executed
            state_manager = get_state_manager()
            active_tasks = state_manager.get_active_tasks()
            
            console.print("[cyan]Task execution in progress...[/cyan]")
            console.print(f"[cyan]Active tasks: {len(active_tasks)}[/cyan]")
            
            # Try to show execution trace
            for task_id in active_tasks:
                exec_state = state_manager.get_execution_state(task_id)
                if exec_state:
                    trace = exec_state.execution_trace
                    console.print(f"\n[bold]Execution Trace:[/bold]")
                    console.print(f"  Status: {trace.status}")
                    console.print(f"  Steps executed: {len(trace.steps_executed)}")
                    for step in trace.steps_executed:
                        status = "✓" if step.get("success") else "✗"
                        console.print(
                            f"    {status} {step.get('description')} "
                            f"({step.get('duration_ms')}ms)"
                        )

    except Exception as e:
        logger.error(f"Error executing task: {e}")
        console.print(f"[red]Error:[/red] {e}")
    finally:
        # Cleanup
        await planner.shutdown()
        await executor.shutdown()
        await verifier.shutdown()
        await reset_bus()


@cli.command()
def agents() -> None:
    """List available agents."""
    state_manager = get_state_manager()
    system_state = state_manager.get_system_state()

    if not system_state.agent_states:
        console.print("[yellow]No agents registered[/yellow]")
        return

    table = Table(title="Agents")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")

    for agent_id, state_data in system_state.agent_states.items():
        table.add_row(
            agent_id,
            state_data.get("type", "unknown"),
            state_data.get("status", "unknown"),
        )

    console.print(table)


@cli.command()
def config() -> None:
    """Show current configuration."""
    settings = get_settings()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Debug Mode", str(settings.debug_mode))
    table.add_row("Dry Run", str(settings.dry_run))
    table.add_row("LLM Provider", settings.llm.provider)
    table.add_row("LLM Model", settings.llm.model_name)
    table.add_row("Planning Depth", str(settings.agent.planning_depth))
    table.add_row("Verification Enabled", str(settings.agent.verification_enabled))
    table.add_row("Data Directory", str(settings.data_dir))

    console.print(table)


@cli.command()
def init() -> None:
    """Initialize the system."""
    console.print("[bold cyan]Initializing Agentic OS...[/bold cyan]")

    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"✓ Data directory: {settings.data_dir}")
    console.print(f"✓ Cache directory: {settings.cache_dir}")
    console.print(f"✓ Logs directory: {settings.logs_dir}")

    console.print("[bold green]✓ Initialization complete[/bold green]")


@cli.command()
def test() -> None:
    """Run system diagnostics."""
    console.print("[bold cyan]Running system diagnostics...[/bold cyan]\n")

    # Test configuration
    try:
        settings = get_settings()
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]✗[/red] Configuration failed: {e}")
        return

    # Test async runtime
    try:
        async def test_async() -> None:
            bus = await get_bus()
            console.print("[green]✓[/green] Message bus running")
            await reset_bus()

        asyncio.run(test_async())
    except Exception as e:
        console.print(f"[red]✗[/red] Async runtime failed: {e}")
        return

    # Test state manager
    try:
        state_manager = get_state_manager()
        console.print("[green]✓[/green] State manager initialized")
    except Exception as e:
        console.print(f"[red]✗[/red] State manager failed: {e}")
        return

    console.print("\n[bold green]All diagnostics passed![/bold green]")


@cli.command()
@click.option(
    "--interval",
    "-i",
    default=60,
    type=int,
    help="Check interval for reminders in seconds (default: 60)"
)
def daemon(interval: int) -> None:
    """Start the Dex reminder daemon (runs in background).
    
    The daemon monitors your reminders and sends notifications when they're due.
    Supported channels: Desktop popup, Email, WhatsApp
    
    Example:
        dex daemon --interval 30     # Check reminders every 30 seconds
        dex daemon                   # Check reminders every 60 seconds (default)
    """
    from agentic_os.daemon.reminder_monitor import run_daemon
    
    console.print("[bold cyan]🤖 Starting Dex Reminder Daemon[/bold cyan]")
    console.print(f"   Check interval: {interval} seconds")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    try:
        asyncio.run(run_daemon(check_interval=interval))
    except KeyboardInterrupt:
        console.print("\n[yellow]Daemon stopped[/yellow]")


@cli.command()
@click.option(
    "--channel",
    "-c",
    type=click.Choice(["desktop", "email", "whatsapp", "all"]),
    default="all",
    help="Which notification channel to test"
)
def notify(channel: str) -> None:
    """Test notification channels.
    
    This sends a test notification to verify your notification setup.
    
    Example:
        dex notify --channel desktop   # Test desktop notification
        dex notify --channel email     # Test email notification
        dex notify --channel whatsapp  # Test WhatsApp notification
        dex notify                     # Test all channels
    """
    from agentic_os.notifications.base import Notification
    from agentic_os.notifications.desktop import DesktopNotifier
    from agentic_os.notifications.email_notifier import EmailNotifier
    from agentic_os.notifications.whatsapp_notifier import WhatsAppNotifier
    
    async def send_test():
        test_notification = Notification(
            title="🤖 Dex Test Notification",
            message="If you're reading this, notifications are working! ✨",
            priority="high",
            tag="test"
        )
        
        results = {}
        
        if channel in ["desktop", "all"]:
            console.print("[cyan]Testing Desktop Notifications...[/cyan]")
            notifier = DesktopNotifier()
            if await notifier.is_configured():
                success = await notifier.send(test_notification)
                results["desktop"] = "✓ Success" if success else "✗ Failed"
            else:
                results["desktop"] = (
                    "⚠ Not available (Windows required)"
                    if notifier.available is False
                    else "⚠ Not configured"
                )
        
        if channel in ["email", "all"]:
            console.print("[cyan]Testing Email Notifications...[/cyan]")
            notifier = EmailNotifier()
            if await notifier.is_configured():
                success = await notifier.send(test_notification)
                results["email"] = "✓ Success" if success else "✗ Failed"
            else:
                results["email"] = (
                    "⚠ Not configured (set NOTIFY_EMAIL_FROM and NOTIFY_SMTP_PASSWORD in .env)"
                )
        
        if channel in ["whatsapp", "all"]:
            console.print("[cyan]Testing WhatsApp Notifications...[/cyan]")
            notifier = WhatsAppNotifier()
            if await notifier.is_configured():
                success = await notifier.send(test_notification)
                results["whatsapp"] = "✓ Success" if success else "✗ Failed"
            else:
                results["whatsapp"] = (
                    "⚠ Not configured (install twilio: pip install twilio, "
                    "set Twilio credentials in .env)"
                )
        
        # Display results
        console.print("\n[bold]Notification Test Results:[/bold]")
        for ch, result in results.items():
            console.print(f"  {ch.capitalize()}: {result}")
    
    try:
        asyncio.run(send_test())
    except Exception as e:
        console.print(f"[red]Error during notification test: {e}[/red]")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
