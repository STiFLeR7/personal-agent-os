"""
Configuration management for the Agentic OS.

This module provides centralized configuration handling with support for
environment-based overrides, type validation, and schema documentation.
"""

from pathlib import Path
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DexIdentity(BaseSettings):
    """Configuration for Dex agent identity and voice integration."""

    model_config = SettingsConfigDict(env_prefix="DEX_")

    name: str = Field(default="Dex", description="Agent name (voice wake word)")
    voice_enabled: bool = Field(default=False, description="Enable voice input/output")
    voice_language: str = Field(default="en-US", description="Voice language for STT/TTS")
    wake_word: str = Field(default="Hey Dex", description="Voice wake phrase")
    personality: str = Field(
        default="helpful and efficient",
        description="Agent personality description for LLM context",
    )
    reminders_enabled: bool = Field(default=True, description="Enable reminder functionality")
    notes_enabled: bool = Field(default=True, description="Enable note-taking")
    time_zone: str = Field(default="UTC", description="Time zone for reminders and scheduling")


class LLMConfig(BaseSettings):
    """Configuration for LLM inference."""

    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: str = Field(default="ollama", description="LLM provider: 'ollama' or 'huggingface'")
    model_name: str = Field(
        default="mistral", description="Model identifier (e.g., 'mistral', 'neural-chat')"
    )
    base_url: Optional[str] = Field(
        default=None, description="Base URL for API (e.g., http://localhost:11434)"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(default=2048, ge=1, description="Maximum tokens to generate")
    timeout: int = Field(default=120, ge=1, description="Request timeout in seconds")


class ToolsConfig(BaseSettings):
    """Configuration for tool integrations."""

    model_config = SettingsConfigDict(env_prefix="TOOLS_")

    gmail_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to Gmail OAuth credentials JSON (auto-cached after first auth)",
    )
    browser_executable: Optional[str] = Field(
        default=None, description="Path to Chrome/Chromium executable"
    )
    browser_headless: bool = Field(default=False, description="Run browser in headless mode")


class LoggingConfig(BaseSettings):
    """Configuration for logging and observability."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    format: str = Field(
        default="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        description="Loguru format string",
    )
    file: Optional[str] = Field(
        default=None, description="Log file path (None = console only)"
    )
    include_timestamps: bool = Field(default=True, description="Include timestamps in logs")
    trace_decisions: bool = Field(
        default=True, description="Log all agent decisions and reasoning"
    )


class AgentConfig(BaseSettings):
    """Configuration for agent behavior."""

    model_config = SettingsConfigDict(env_prefix="AGENT_")

    planning_depth: int = Field(
        default=5, ge=1, le=20, description="Max reasoning depth for planners"
    )
    verification_enabled: bool = Field(
        default=True, description="Enable execution verification steps"
    )
    self_correction_attempts: int = Field(
        default=3, ge=1, le=10, description="Max retries on failure"
    )
    request_timeout: int = Field(
        default=300, ge=30, description="Max seconds per agent request"
    )


class Settings(BaseSettings):
    """Root configuration for the entire system."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # System paths
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    data_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".agentic_os",
        description="Directory for caches, logs, and persistent state",
    )
    cache_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".agentic_os" / "cache"
    )
    logs_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".agentic_os" / "logs"
    )

    # Subsystem configs
    dex: DexIdentity = Field(default_factory=DexIdentity)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)

    # Runtime flags
    debug_mode: bool = Field(default=False, description="Enable debug logging and tracing")
    dry_run: bool = Field(
        default=False, description="Simulate tool execution without side effects"
    )

    def model_post_init(self, __context):  # type: ignore[no-untyped-def]
        """Create necessary directories after model initialization."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Enable debug mode logging if requested
        if self.debug_mode:
            self.logging.level = "DEBUG"


# Global singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None
