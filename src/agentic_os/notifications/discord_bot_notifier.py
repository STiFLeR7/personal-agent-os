"""Discord Bot REST API notification channel implementation."""

import aiohttp
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from agentic_os.notifications.base import Notification, NotificationHandler
from agentic_os.config import get_settings

logger = logging.getLogger(__name__)


class DiscordBotNotifier(NotificationHandler):
    """Send notifications to Discord via Bot REST API (Hermes-style)."""
    
    def __init__(self):
        """Initialize Discord bot notifier."""
        self.settings = get_settings()
        self.bot_token = self.settings.discord.bot_token
        self.guild_id = self.settings.discord.guild_id
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        self.available = self.bot_token is not None
        self._channel_cache: Dict[str, str] = {}
    
    async def is_configured(self) -> bool:
        """Check if Discord bot token is configured."""
        return self.bot_token is not None
    
    async def _get_channel_id(self, session: aiohttp.ClientSession, channel_name: str) -> Optional[str]:
        """Resolve a channel name to an ID for the configured guild."""
        if channel_name in self._channel_cache:
            return self._channel_cache[channel_name]
            
        if not self.guild_id:
            logger.warning("DISCORD_GUILD_ID not set, cannot resolve channel names")
            return None
            
        url = f"{self.base_url}/guilds/{self.guild_id}/channels"
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    channels = await response.json()
                    for ch in channels:
                        if ch.get("name") == channel_name.replace("#", ""):
                            self._channel_cache[channel_name] = ch["id"]
                            return ch["id"]
                    logger.warning(f"Channel '{channel_name}' not found in guild {self.guild_id}")
                else:
                    err = await response.text()
                    logger.error(f"Failed to fetch channels: {response.status} - {err}")
        except Exception as e:
            logger.error(f"Error fetching Discord channels: {e}")
            
        return None

    async def send(self, notification: Notification) -> bool:
        """
        Send notification to Discord via Bot API.
        
        Args:
            notification: Notification object
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bot_token:
            logger.debug("Discord bot token not configured, skipping")
            return False
            
        # Select color based on priority
        color = 0x34C759  # Green (Dex Default)
        if notification.priority == "high":
            color = 0xFF3B30  # Red
        elif notification.priority == "medium":
            color = 0xFF9F0A  # Orange
            
        # Target channel from tag or settings
        target_channel_name = notification.tag or self.settings.discord.reminders_channel or "reminders"
        
        now = datetime.now(timezone.utc)
        
        # Build thumbnail URL if RENDER_EXTERNAL_URL is set
        thumbnail_url = None
        if self.settings.render_external_url:
            thumbnail_url = f"{self.settings.render_external_url.rstrip('/')}/assets/dex-icon.svg"

        payload = {
            "embeds": [
                {
                    "title": notification.title,
                    "description": notification.message,
                    "color": color,
                    "footer": {
                        "text": f"Dex Cognitive OS • {notification.tag}"
                    },
                    "thumbnail": {"url": thumbnail_url} if thumbnail_url else None,
                    "timestamp": now.isoformat()
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                channel_id = await self._get_channel_id(session, target_channel_name)
                if not channel_id:
                    # Fallback to general if specified, or just fail
                    logger.warning(f"Could not resolve channel {target_channel_name}, falling back to system logic")
                    return False
                    
                url = f"{self.base_url}/channels/{channel_id}/messages"
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status in (200, 201, 204):
                        logger.info(f"Discord Bot notification sent to #{target_channel_name}: {notification.title}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Discord Bot notification: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error sending Discord Bot notification: {e}")
            return False
