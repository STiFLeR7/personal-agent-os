"""Discord bot gateway for Dex."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional

try:
    import discord
    from discord import app_commands
    from discord.ext import commands
except ImportError:
    discord = None

from loguru import logger

from agentic_os.config import get_settings
from agentic_os.core import ExecutorAgent, PlannerAgent, VerifierAgent
from agentic_os.core.memory import ContextMemoryEngine
from agentic_os.core.risk import RiskEngine
from agentic_os.coordination.bus import get_bus
from agentic_os.coordination.messages import TaskDefinition
from agentic_os.discord.embed import DexEmbedPayload, build_embed
from agentic_os.discord.logging import log_discord_event
from agentic_os.tools import (
    AppLaunchTool,
    BrowserOpenTool,
    EmailComposeTool,
    FileReadTool,
    FileWriteTool,
    NoteCreateTool,
    NoteListTool,
    ReminderListTool,
    ReminderSetTool,
    ShellCommandTool,
    GenericChatTool,
    get_tool_registry,
)

if TYPE_CHECKING:
    from agentic_os.coordination.messages import ExecutionPlan


class PendingPlan:
    """Represents a plan waiting for user confirmation."""

    def __init__(self, task_id: str, plan: "ExecutionPlan", interaction: "discord.Interaction"):
        self.task_id = task_id
        self.plan = plan
        self.interaction = interaction
        self.created_at = datetime.now(timezone.utc)


class DexCog(commands.GroupCog, name="dex"):
    """Main Dex command group."""

    def __init__(self, bot: DexDiscordBot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="status", description="Show Dex status")
    async def status(self, interaction: discord.Interaction) -> None:
        if not self.bot._is_console_channel(interaction):
            await interaction.response.send_message(
                embed=build_embed(
                    DexEmbedPayload(
                        title="Dex • Channel Restricted",
                        summary="Commands must be issued in the console channel.",
                        risk_level="low",
                        execution_plan=[],
                        tools_used=[],
                        latency_ms=None,
                        token_usage=None,
                        verification_status="blocked",
                    )
                ),
                ephemeral=True,
            )
            return

        current_mode = self.bot._memory.get_session_context("mode") or "default"
        await interaction.response.send_message(
            embed=build_embed(
                DexEmbedPayload(
                    title="Dex • Status",
                    summary=f"Dex Discord gateway is online. Active mode: {current_mode}.",
                    risk_level="low",
                    execution_plan=[],
                    tools_used=[],
                    latency_ms=None,
                    token_usage=None,
                    verification_status="n/a",
                )
            )
        )

    @app_commands.command(name="mode", description="Set Dex operating mode")
    @app_commands.describe(mode="Operating mode (e.g. default, creative, strict)")
    async def mode(self, interaction: discord.Interaction, mode: str) -> None:
        if not self.bot._is_console_channel(interaction):
            await interaction.response.send_message(
                embed=build_embed(
                    DexEmbedPayload(
                        title="Dex • Channel Restricted",
                        summary="Commands must be issued in the console channel.",
                        risk_level="low",
                        execution_plan=[],
                        tools_used=[],
                        latency_ms=None,
                        token_usage=None,
                        verification_status="blocked",
                    )
                ),
                ephemeral=True,
            )
            return

        self.bot._memory.set_session_context("mode", mode)
        await interaction.response.send_message(
            embed=build_embed(
                DexEmbedPayload(
                    title="Dex • Mode Updated",
                    summary=f"Active mode set to '{mode}'.",
                    risk_level="low",
                    execution_plan=[],
                    tools_used=["session_context"],
                    latency_ms=None,
                    token_usage=None,
                    verification_status="n/a",
                )
            )
        )

    @app_commands.command(name="run", description="Run a Dex task")
    @app_commands.describe(command="Task description")
    async def run(self, interaction: discord.Interaction, command: str) -> None:
        if not self.bot._is_console_channel(interaction):
            await interaction.response.send_message(
                embed=build_embed(
                    DexEmbedPayload(
                        title="Dex • Channel Restricted",
                        summary="Commands must be issued in the console channel.",
                        risk_level="low",
                        execution_plan=[],
                        tools_used=[],
                        latency_ms=None,
                        token_usage=None,
                        verification_status="blocked",
                    )
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        log_discord_event(
            "command_received",
            {"command": command, "user_id": interaction.user.id, "channel": interaction.channel_id},
        )

        await self.bot._ensure_agents()

        task = TaskDefinition(
            id=uuid.uuid4(),
            user_request=command,
            context={"source": "discord", "user_id": str(interaction.user.id)},
        )

        try:
            plan = await self.bot._planner.plan_task(task)
            risk_report = self.bot._risk_engine.analyze_plan(plan)

            if risk_report.risk_level == "high":
                self.bot.pending_confirmations[str(task.id)] = PendingPlan(str(task.id), plan, interaction)
                
                embed_payload = build_embed(
                    DexEmbedPayload(
                        title="Dex • High Risk Action Required",
                        summary="This task requires high-risk operations. Please confirm execution.",
                        risk_level="high",
                        execution_plan=[f"{s.order}. {s.description}" for s in plan.steps],
                        tools_used=list(set(s.tool_name for s in plan.steps)),
                        latency_ms=None,
                        token_usage=None,
                        verification_status="pending_confirmation",
                    )
                )
                await interaction.followup.send(embed=embed_payload, view=ConfirmView(self.bot, str(task.id)))
                await self.bot._post_to_channel("priority-feed", embed_payload)
            else:
                await interaction.followup.send(
                    embed=build_embed(
                        DexEmbedPayload(
                            title="Dex • Task Initialized",
                            summary="Executing low-risk autonomous task.",
                            risk_level=risk_report.risk_level,
                            execution_plan=[f"{s.order}. {s.description}" for s in plan.steps],
                            tools_used=list(set(s.tool_name for s in plan.steps)),
                            latency_ms=None,
                            token_usage=None,
                            verification_status="executing",
                        )
                    )
                )
                
                result = await self.bot._executor.execute_plan(plan)
                verification = await self.bot._verifier.verify_execution(plan, result)
                
                embed_payload = build_embed(
                    DexEmbedPayload(
                        title="Dex • Task Complete",
                        summary=verification.summary,
                        risk_level=risk_report.risk_level,
                        execution_plan=[f"{s.order}. {s.description}" for s in plan.steps],
                        tools_used=list(set(s.tool_name for s in plan.steps)),
                        latency_ms=result.latency_ms,
                        token_usage=str(result.token_usage),
                        verification_status="verified" if verification.success else "failed",
                    )
                )
                await interaction.followup.send(embed=embed_payload)
                await self.bot._post_to_channel("timeline", embed_payload)

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}")


class MemoryCog(commands.GroupCog, name="memory"):
    """Memory management tools."""

    def __init__(self, bot: DexDiscordBot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="search", description="Search Dex memory")
    @app_commands.describe(query="Search query")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        if not self.bot._is_console_channel(interaction):
            await interaction.response.send_message(
                embed=build_embed(
                    DexEmbedPayload(
                        title="Dex • Channel Restricted",
                        summary="Commands must be issued in the console channel.",
                        risk_level="low",
                        execution_plan=[],
                        tools_used=[],
                        latency_ms=None,
                        token_usage=None,
                        verification_status="blocked",
                    )
                ),
                ephemeral=True,
            )
            return

        results = self.bot._memory.search_semantic(query, limit=5)
        if not results:
            summary = "No memory matches found."
            plan_lines = []
        else:
            summary = "Top memory matches:"
            plan_lines = [f"{idx + 1}. {r.content[:120]}" for idx, r in enumerate(results)]

        await interaction.response.send_message(
            embed=build_embed(
                DexEmbedPayload(
                    title="Dex • Memory Search",
                    summary=summary,
                    risk_level="low",
                    execution_plan=plan_lines,
                    tools_used=["memory_search"],
                    latency_ms=None,
                    token_usage=None,
                    verification_status="n/a",
                )
            )
        )


class ConfirmView(discord.ui.View):
    """View for confirming high-risk actions."""

    def __init__(self, bot: DexDiscordBot, task_id: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.task_id = task_id

    @discord.ui.button(label="Confirm Execution", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        pending = self.bot.pending_confirmations.pop(self.task_id, None)
        if not pending:
            await interaction.response.send_message("Confirmation expired or invalid.", ephemeral=True)
            return

        await interaction.response.edit_message(content="✅ Execution confirmed. Processing...", view=None)
        
        result = await self.bot._executor.execute_plan(pending.plan)
        verification = await self.bot._verifier.verify_execution(pending.plan, result)
        
        embed_payload = build_embed(
            DexEmbedPayload(
                title="Dex • Task Complete",
                summary=verification.summary,
                risk_level="high",
                execution_plan=[f"{s.order}. {s.description}" for s in pending.plan.steps],
                tools_used=list(set(s.tool_name for s in pending.plan.steps)),
                latency_ms=result.latency_ms,
                token_usage=str(result.token_usage),
                verification_status="verified" if verification.success else "failed",
            )
        )
        await interaction.followup.send(embed=embed_payload)
        await self.bot._post_to_channel("timeline", embed_payload)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.pending_confirmations.pop(self.task_id, None)
        await interaction.response.edit_message(content="❌ Execution cancelled.", view=None)


class DexDiscordBot(commands.Bot):
    """Dex Discord bot implementation."""

    def __init__(self) -> None:
        settings = get_settings()
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, description="Dex AI Personal Operator")
        self.settings = settings
        self.pending_confirmations: Dict[str, PendingPlan] = {}
        self._bus = None
        self._planner: Optional[PlannerAgent] = None
        self._executor: Optional[ExecutorAgent] = None
        self._verifier: Optional[VerifierAgent] = None
        self._risk_engine = RiskEngine()
        self._memory = ContextMemoryEngine()

    async def _post_to_channel(self, channel_name: str, embed: "discord.Embed") -> None:
        """Helper to post to a specific channel by name."""
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == channel_name:
                    try:
                        await channel.send(embed=embed)
                        return
                    except Exception as e:
                        logger.error(f"Failed to post to {channel_name}: {e}")

    async def setup_hook(self) -> None:
        # Load Cogs
        await self.add_cog(DexCog(self))
        await self.add_cog(MemoryCog(self))

        # Sync commands
        guild_id = self.settings.discord.guild_id
        if guild_id:
            await self.tree.sync(guild=discord.Object(id=guild_id))
            logger.info(f"Synced slash commands to guild {guild_id}")
        else:
            await self.tree.sync()
            logger.info("Synced slash commands globally")

    async def close(self) -> None:
        if self._planner:
            await self._planner.shutdown()
        if self._executor:
            await self._executor.shutdown()
        if self._verifier:
            await self._verifier.shutdown()
        await super().close()

    async def _ensure_agents(self) -> None:
        if self._bus is not None:
            return

        self._bus = await get_bus()
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
            GenericChatTool(),
        ]
        for tool in tools:
            try:
                registry.register(tool)
            except ValueError:
                pass

        self._planner = PlannerAgent()
        self._executor = ExecutorAgent()
        self._verifier = VerifierAgent()

        await self._planner.initialize(self._bus)
        await self._executor.initialize(self._bus)
        await self._verifier.initialize(self._bus)

    def _is_console_channel(self, interaction: "discord.Interaction") -> bool:
        channel = interaction.channel
        if channel is None:
            return False
        return getattr(channel, "name", None) == self.settings.discord.console_channel


def run_discord_bot() -> None:
    """Run the Dex Discord bot."""
    if discord is None:
        logger.error("discord.py is not installed. Install with `pip install discord.py`.")
        return

    settings = get_settings()
    if not settings.discord.bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required to run the bot.")

    bot = DexDiscordBot()
    bot.run(settings.discord.bot_token)


if __name__ == "__main__":
    run_discord_bot()
