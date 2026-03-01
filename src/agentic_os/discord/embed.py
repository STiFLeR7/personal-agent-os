"""Discord embed helpers for Dex responses."""

from dataclasses import dataclass
from typing import List, Optional

try:
    import discord
except Exception:  # pragma: no cover - optional dependency
    discord = None  # type: ignore[assignment]


@dataclass
class DexEmbedPayload:
    """Structured response payload for Discord embeds."""

    title: str
    summary: str
    risk_level: str
    execution_plan: List[str]
    tools_used: List[str]
    latency_ms: Optional[int]
    token_usage: Optional[str]
    verification_status: str


def _risk_color(risk_level: str) -> int:
    if risk_level == "high":
        return 0xFF3B30
    if risk_level == "medium":
        return 0xFF9F0A
    return 0x34C759


def build_embed(payload: DexEmbedPayload) -> "discord.Embed":
    """Build a Discord embed that matches the required response format."""
    if discord is None:
        raise RuntimeError("discord.py is required to build Discord embeds")

    embed = discord.Embed(
        title=payload.title,
        description=payload.summary,
        color=_risk_color(payload.risk_level),
    )
    embed.add_field(name="Risk Level", value=payload.risk_level.upper(), inline=True)
    embed.add_field(
        name="Execution Plan",
        value="\n".join(payload.execution_plan) if payload.execution_plan else "None",
        inline=False,
    )
    embed.add_field(
        name="Tools Used",
        value=", ".join(payload.tools_used) if payload.tools_used else "None",
        inline=False,
    )
    embed.add_field(
        name="Latency",
        value=f"{payload.latency_ms} ms" if payload.latency_ms is not None else "n/a",
        inline=True,
    )
    embed.add_field(
        name="Token Usage",
        value=payload.token_usage or "n/a",
        inline=True,
    )
    embed.add_field(
        name="Verification Status",
        value=payload.verification_status,
        inline=True,
    )
    return embed
