"""
Configuration management for the Agentic OS.

This module provides centralized configuration handling with support for
environment-based overrides, type validation, and schema documentation.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file explicitly
load_dotenv()


class DexIdentity(BaseModel):

    """Configuration for Dex agent identity and voice integration."""

    name: str = Field(default="Dex")
    voice_enabled: bool = Field(default=False)
    voice_language: str = Field(default="en-US")
    wake_word: str = Field(default="Hey Dex")
    personality: str = Field(default="helpful and efficient")
    reminders_enabled: bool = Field(default=True)
    notes_enabled: bool = Field(default=True)
    time_zone: str = Field(default="UTC")


class LLMConfig(BaseModel):
    """Configuration for LLM inference."""

    provider: str = Field(
        default="ollama", 
        validation_alias=AliasChoices("LLM_PROVIDER", "provider")
    )
    model_name: str = Field(
        default="gemini-1.5-flash-latest", 
        validation_alias=AliasChoices("LLM_MODEL_NAME", "model_name")
    )

    api_key: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("LLM_API_KEY", "api_key", "GEMINI_API_KEY")
    )
    discord_webhook_url: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("LLM_DISCORD_WEBHOOK_URL", "discord_webhook_url")
    )
    base_url: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("LLM_BASE_URL", "base_url")
    )
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)
    timeout: int = Field(default=120)


class NotificationConfig(BaseModel):
    """Configuration for notification channels."""

    desktop_enabled: bool = Field(default=True)
    email_enabled: bool = Field(
        default=False, 
        validation_alias=AliasChoices("NOTIFY_EMAIL_ENABLED", "email_enabled")
    )
    whatsapp_enabled: bool = Field(
        default=False, 
        validation_alias=AliasChoices("NOTIFY_WHATSAPP_ENABLED", "whatsapp_enabled")
    )
    
    # Email settings
    email_from: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("NOTIFY_EMAIL_FROM", "email_from")
    )
    smtp_server: str = Field(
        default="smtp.gmail.com", 
        validation_alias=AliasChoices("NOTIFY_SMTP_SERVER", "smtp_server")
    )
    smtp_port: int = Field(
        default=587, 
        validation_alias=AliasChoices("NOTIFY_SMTP_PORT", "smtp_port")
    )
    smtp_password: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("NOTIFY_SMTP_PASSWORD", "smtp_password")
    )
    
    # WhatsApp/Twilio settings
    twilio_account_sid: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("NOTIFY_TWILIO_ACCOUNT_SID", "twilio_account_sid")
    )
    twilio_auth_token: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("NOTIFY_TWILIO_AUTH_TOKEN", "twilio_auth_token")
    )
    twilio_whatsapp_from: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("NOTIFY_TWILIO_WHATSAPP_FROM", "twilio_whatsapp_from")
    )
    user_whatsapp_number: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("NOTIFY_USER_WHATSAPP_NUMBER", "user_whatsapp_number")
    )


class ToolsConfig(BaseModel):
    """Configuration for tool integrations."""

    gmail_credentials_path: Optional[str] = Field(default=None)
    browser_executable: Optional[str] = Field(default=None)
    browser_headless: bool = Field(default=False)


class DiscordConfig(BaseModel):
    """Configuration for Discord bot and webhook integration."""

    bot_token: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("DISCORD_BOT_TOKEN", "bot_token")
    )
    guild_id: Optional[int] = Field(
        default=None, 
        validation_alias=AliasChoices("DISCORD_GUILD_ID", "DISCORD_SERVER_ID", "guild_id")
    )
    webhook_url: Optional[str] = Field(
        default=None, 
        validation_alias=AliasChoices("DISCORD_WEBHOOK_URL", "webhook_url")
    )
    console_channel: str = Field(
        default="console", 
        validation_alias=AliasChoices("DISCORD_CONSOLE_CHANNEL", "console_channel")
    )
    timeline_channel: str = Field(
        default="timeline", 
        validation_alias=AliasChoices("DISCORD_TIMELINE_CHANNEL", "timeline_channel")
    )
    system_logs_channel: str = Field(
        default="system-logs", 
        validation_alias=AliasChoices("DISCORD_SYSTEM_LOGS_CHANNEL", "system_logs_channel")
    )
    priority_feed_channel: str = Field(
        default="priority-feed", 
        validation_alias=AliasChoices("DISCORD_PRIORITY_FEED_CHANNEL", "priority_feed_channel")
    )


class LoggingConfig(BaseModel):
    """Configuration for logging and observability."""

    level: str = Field(default="INFO")
    format: str = Field(
        default="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    file: Optional[str] = Field(default=None)
    include_timestamps: bool = Field(default=True)
    trace_decisions: bool = Field(default=True)


class AgentConfig(BaseModel):
    """Configuration for agent behavior."""

    planning_depth: int = Field(default=5)
    verification_enabled: bool = Field(default=True)
    self_correction_attempts: int = Field(default=3)
    request_timeout: int = Field(default=300)


class Settings(BaseSettings):
    """Root configuration for the entire system."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="_",
        populate_by_name=True
    )

    # System paths
    workspace_root: Path = Field(default_factory=lambda: Path.cwd())
    data_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".agentic_os"
    )
    cache_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".agentic_os" / "cache"
    )
    logs_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".agentic_os" / "logs"
    )
    discord_logs_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".agentic_os" / "discord_logs"
    )

    # Subsystem configs - renamed to match .env prefixes
    dex: DexIdentity = DexIdentity()
    llm: LLMConfig = LLMConfig()
    notify: NotificationConfig = NotificationConfig()
    tools: ToolsConfig = ToolsConfig()
    discord: DiscordConfig = DiscordConfig()
    log: LoggingConfig = LoggingConfig()
    agent: AgentConfig = AgentConfig()

    @property
    def notifications(self) -> NotificationConfig:
        return self.notify

    @property
    def logging(self) -> LoggingConfig:
        return self.log





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
        self.discord_logs_dir.mkdir(parents=True, exist_ok=True)

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
        
        # Manual Overrides for Reliability (ensures .env variables are picked up)
        if not _settings.llm.api_key:
            _settings.llm.api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
        
        if not _settings.llm.provider or _settings.llm.provider == "ollama":
            # If GEMINI_API_KEY is present, default provider to google
            if os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY"):
                _settings.llm.provider = "google"
                _settings.llm.model_name = os.environ.get("LLM_MODEL_NAME") or "gemini-1.5-flash"

        if not _settings.notify.email_from:
            _settings.notify.email_from = os.environ.get("NOTIFY_EMAIL_FROM")
        
        if not _settings.notify.smtp_password:
            _settings.notify.smtp_password = os.environ.get("NOTIFY_SMTP_PASSWORD")

        if not _settings.discord.bot_token:
            _settings.discord.bot_token = os.environ.get("DISCORD_BOT_TOKEN")
            
        if not _settings.discord.guild_id and os.environ.get("DISCORD_GUILD_ID"):
            try:
                _settings.discord.guild_id = int(os.environ.get("DISCORD_GUILD_ID"))
            except:
                pass

        if not _settings.discord.webhook_url:
            _settings.discord.webhook_url = os.environ.get("DISCORD_WEBHOOK_URL") or os.environ.get("LLM_DISCORD_WEBHOOK_URL")

    return _settings



def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None


def load_config() -> Settings:
    """Alias for get_settings() for backward compatibility."""
    return get_settings()
