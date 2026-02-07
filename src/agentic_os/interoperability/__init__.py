"""Interoperability layer for agent-to-agent communication."""

from pydantic import BaseModel, Field


class AgentIdentity(BaseModel):
    """Identity information for an agent in the system."""

    agent_id: str = Field(description="Unique agent identifier")
    agent_type: str = Field(description="Type/role of agent")
    capabilities: list[str] = Field(default_factory=list, description="List of tools available")
    endpoint: str = Field(
        description="Network endpoint (for future remote agent support)"
    )


class PermissionScope(BaseModel):
    """Permission scope for agent authorization."""

    agent_id: str = Field(description="Agent being granted permissions")
    allowed_tools: list[str] = Field(
        default_factory=list, description="Name of tools allowed to call"
    )
    allowed_recipients: list[str] = Field(
        default_factory=list, description="Agent IDs that can be contacted"
    )
    read_resources: list[str] = Field(
        default_factory=list, description="Resources allowed to read"
    )
    write_resources: list[str] = Field(
        default_factory=list, description="Resources allowed to write"
    )


__all__ = ["AgentIdentity", "PermissionScope"]
