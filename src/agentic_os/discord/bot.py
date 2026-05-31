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
from agentic_os.core.telemetry import TelemetryManager
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
from agentic_os.tools.todos import TODOTool

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
        if not self.bot._is_interactive_channel(interaction.channel):
            await interaction.response.send_message("⚠️ This command is restricted to interactive channels.", ephemeral=True)
            return

        current_mode = self.bot._memory.get_session_context("mode") or "default"
        status_text = f"⚡ **Dex Cognitive OS** is online and operational.\n**Active Mode:** `{current_mode}`"
        await interaction.response.send_message(content=status_text)

    @app_commands.command(name="mode", description="Set Dex operating mode")
    @app_commands.describe(mode="Operating mode (e.g. default, creative, strict)")
    async def mode(self, interaction: discord.Interaction, mode: str) -> None:
        if not self.bot._is_interactive_channel(interaction.channel):
            await interaction.response.send_message("⚠️ This command is restricted to interactive channels.", ephemeral=True)
            return

        self.bot._memory.set_session_context("mode", mode)
        await interaction.response.send_message(content=f"✅ Active mode updated to `{mode}`.")

    @app_commands.command(name="run", description="Run a Dex task")
    @app_commands.describe(command="Task description")
    async def run(self, interaction: discord.Interaction, command: str) -> None:
        if not self.bot._is_interactive_channel(interaction.channel):
            await interaction.response.send_message("⚠️ This command is restricted to interactive channels.", ephemeral=True)
            return

        # Simple Rate Limiting (5 seconds per user)
        user_id = interaction.user.id
        now = datetime.now(timezone.utc)
        if user_id in self.bot.cooldowns:
            delta = (now - self.bot.cooldowns[user_id]).total_seconds()
            if delta < 5:
                await interaction.response.send_message(f"⚠️ Please wait {5 - int(delta)}s before your next request.", ephemeral=True)
                return
        self.bot.cooldowns[user_id] = now

        await interaction.response.defer()
        await self.bot._process_dex_request(interaction, command)

    @app_commands.command(name="telemetry", description="Show Dex system telemetry")
    async def telemetry(self, interaction: discord.Interaction) -> None:
        if not self.bot._is_interactive_channel(interaction.channel):
            return

        metrics = self.bot.telemetry.get_metrics_summary()
        
        telemetry_text = (
            "📊 **Dex System Telemetry**\n"
            f"• Total Tasks: `{metrics.get('total_tasks', 0)}`\n"
            f"• Success Rate: `{metrics.get('success_rate', 0):.1%}`\n"
            f"• Active Tools: `{', '.join(list(metrics.get('tool_usage', {}).keys())) or 'None'}`"
        )
        await interaction.response.send_message(content=telemetry_text)


class MemoryCog(commands.GroupCog, name="memory"):
    """Memory management tools."""

    def __init__(self, bot: DexDiscordBot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="search", description="Search Dex memory")
    @app_commands.describe(query="Search query")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        if not self.bot._is_interactive_channel(interaction.channel):
            await interaction.response.send_message("⚠️ This command is restricted to interactive channels.", ephemeral=True)
            return

        results = self.bot._memory.search_semantic(query, limit=5)
        if not results:
            response_text = "❌ No memory matches found."
        else:
            matches = "\n".join([f"• {r.content[:120]}..." for r in results])
            response_text = f"🧠 **Top memory matches for:** `{query}`\n{matches}"

        await interaction.response.send_message(content=response_text)


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

        # Reply to user with plain text summary
        await interaction.followup.send(content=verification.summary)

        # Send technical audit to system-logs and timeline
        await self.bot._post_to_channel("system-logs", embed_payload)
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
        self.cooldowns: Dict[int, datetime] = {}
        self._bus = None
        self._planner: Optional[PlannerAgent] = None
        self._executor: Optional[ExecutorAgent] = None
        self._verifier: Optional[VerifierAgent] = None
        self._risk_engine = RiskEngine()
        self._memory = ContextMemoryEngine()
        self.telemetry = TelemetryManager()

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"✨ Dex Discord Bot is online as {self.user} (ID: {self.user.id})")
        logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        logger.info(f"📡 Status: Operational (Interactivity enabled server-wide)")

    async def on_message(self, message: discord.Message) -> None:
        """Handle conversational pings."""
        if message.author.bot:
            return

        # Check if the bot was pinged
        bot_pinged = self.user.mentioned_in(message)
        is_interactive = self._is_interactive_channel(message.channel)
        
        logger.debug(f"Message received in #{getattr(message.channel, 'name', 'DM')}: {message.content[:50]}... (Pinged: {bot_pinged}, Interactive: {is_interactive})")

        # Respond if pinged in an interactive channel
        if bot_pinged and is_interactive:
            # Use regex to clean ALL bot mentions (id, nickname, etc.)
            import re
            clean_content = re.sub(f"<@!?{self.user.id}>", "", message.content).strip()
            
            if clean_content:
                logger.info(f"Conversational request from {message.author}: {clean_content}")
                async with message.channel.typing():
                    await self._process_dex_request(message, clean_content)
            else:
                # If just a ping with no text, give a status update
                await message.reply("⚡ Dex Cognitive OS is online and operational. How can I help?")
        
        await self.process_commands(message)

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

    async def _process_dex_request(self, target: discord.Interaction | discord.Message, command: str):
        """Internal logic to process a task request from any Discord source."""
        log_discord_event(
            "command_received",
            {"command": command, "user_id": target.author.id if isinstance(target, discord.Message) else target.user.id},
        )

        await self._ensure_agents()

        task = TaskDefinition(
            id=uuid.uuid4(),
            user_request=command,
            context={"source": "discord", "user_id": str(target.author.id if isinstance(target, discord.Message) else target.user.id)},
        )

        try:
            plan = await self._planner.plan_task(task)
            if not plan:
                err_summary = "I couldn't figure out how to handle this request."
                err_embed = build_embed(DexEmbedPayload(
                    title="Dex • Planning Failed",
                    summary=err_summary,
                    risk_level="low", execution_plan=[], tools_used=[],
                    latency_ms=None, token_usage=None, verification_status="error"
                ))

                if isinstance(target, discord.Interaction):
                    await target.followup.send(content=f"⚠️ {err_summary}")
                else:
                    await target.reply(content=f"⚠️ {err_summary}")

                await self._post_to_channel("system-logs", err_embed)
                return

            risk_report = self._risk_engine.analyze_plan(plan)

            if risk_report.risk_level == "high":
                self.pending_confirmations[str(task.id)] = PendingPlan(str(task.id), plan, target if isinstance(target, discord.Interaction) else None)
                embed_payload = build_embed(DexEmbedPayload(
                    title="Dex • High Risk Action Required",
                    summary="Please confirm execution of this high-risk task.",
                    risk_level="high",
                    execution_plan=[f"{s.order}. {s.description}" for s in plan.steps],
                    tools_used=list(set(s.tool_name for s in plan.steps)),
                    latency_ms=None, token_usage=None, verification_status="pending_confirmation"
                ))

                confirm_text = "⚠️ **High-Risk Action Required**\nI've generated a plan that requires manual confirmation. Please review and confirm below."
                if isinstance(target, discord.Interaction):
                    await target.followup.send(content=confirm_text, view=ConfirmView(self, str(task.id)))
                else:
                    await target.reply(content=confirm_text, view=ConfirmView(self, str(task.id)))

                await self._post_to_channel("priority-feed", embed_payload)
                await self._post_to_channel("system-logs", embed_payload)
            else:
                result = await self._executor.execute_plan(plan)
                verification = await self._verifier.verify_execution(plan, result)
                embed_payload = build_embed(
                    DexEmbedPayload(
                        title="Dex • Task Complete",
                        summary=verification.summary,
                        risk_level=risk_report.risk_level,
                        execution_plan=[f"{s.order}. {s.description}" for s in plan.steps],
                        tools_used=list(set(s.tool_name for s in plan.steps)),
                        latency_ms=result.latency_ms, token_usage=str(result.token_usage),
                        verification_status="verified" if verification.success else "failed"
                    )
                )

                # Reply to user with plain text summary
                response_text = verification.summary
                if isinstance(target, discord.Interaction):
                    await target.followup.send(content=response_text)
                else:
                    await target.reply(content=response_text)

                # Send technical audit to system-logs and timeline
                await self._post_to_channel("system-logs", embed_payload)
                await self._post_to_channel("timeline", embed_payload)

        except Exception as e:
            logger.error(f"Error processing request: {e}")

    async def setup_hook(self) -> None:
        await self.add_cog(DexCog(self))
        await self.add_cog(MemoryCog(self))
        guild_id = self.settings.discord.guild_id
        if guild_id:
            await self.tree.sync(guild=discord.Object(id=guild_id))
        else:
            await self.tree.sync()

    async def close(self) -> None:
        if self._planner: await self._planner.shutdown()
        if self._executor: await self._executor.shutdown()
        if self._verifier: await self._verifier.shutdown()
        await super().close()

    async def _ensure_agents(self) -> None:
        if self._bus is not None: return
        self._bus = await get_bus()
        registry = get_tool_registry()
        tools = [
            ShellCommandTool(), FileReadTool(), FileWriteTool(), NoteCreateTool(), NoteListTool(),
            ReminderSetTool(), ReminderListTool(), EmailComposeTool(), BrowserOpenTool(), AppLaunchTool(),
            GenericChatTool(), TODOTool()
        ]
        for t in tools:
            try: registry.register(t)
            except ValueError: pass

        self._planner, self._executor, self._verifier = PlannerAgent(), ExecutorAgent(), VerifierAgent()
        await self._planner.initialize(self._bus)
        await self._executor.initialize(self._bus)
        await self._verifier.initialize(self._bus)

    def _is_interactive_channel(self, channel: discord.abc.Messageable) -> bool:
        # ALLOW ALL CHANNELS FOR DEBUGGING (Hermes everywhere)
        return True


def run_discord_bot() -> None:
    settings = get_settings()
    if not settings.discord.bot_token: raise RuntimeError("DISCORD_BOT_TOKEN is required.")
    bot = DexDiscordBot()
    bot.run(settings.discord.bot_token)


if __name__ == "__main__":
    run_discord_bot()
