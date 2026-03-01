"""Discord notification channel implementation."""

import aiohttp
import logging
from typing import Optional
from agentic_os.notifications.base import Notification, NotificationHandler
from agentic_os.config import get_settings

logger = logging.getLogger(__name__)


class DiscordNotifier(NotificationHandler):
    """Send notifications to Discord via Webhooks."""
    
    def __init__(self):
        """Initialize Discord notifier."""
        settings = get_settings()
        # Prefer DISCORD_WEBHOOK_URL, fall back to legacy LLM_DISCORD_WEBHOOK_URL
        self.webhook_url = settings.discord.webhook_url or settings.llm.discord_webhook_url
        self.available = self.webhook_url is not None
    
    async def is_configured(self) -> bool:
        """Check if Discord webhook is configured."""
        return self.webhook_url is not None
    
    async def send(self, notification: Notification) -> bool:
        """
        Send notification to Discord.
        
        Args:
            notification: Notification object
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.debug("Discord webhook not configured, skipping")
            return False
            
        # Select color based on priority
        color = 0x34C759  # Green
        if notification.priority == "high":
            color = 0xFF3B30  # Red
        elif notification.priority == "medium":
            color = 0xFF9F0A  # Orange
            
        payload = {
            "embeds": [
                {
                    "title": notification.title,
                    "description": notification.message,
                    "color": color,
                    "footer": {
                        "text": f"Dex Cognitive OS • {notification.tag}"
                    }
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status in (200, 204):
                        logger.info(f"Discord notification sent: {notification.title}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Discord notification: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False
