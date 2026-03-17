"""Resend notification channel implementation."""

import aiohttp
import logging
from typing import Optional
from agentic_os.notifications.base import Notification, NotificationHandler
from agentic_os.config import get_settings

logger = logging.getLogger(__name__)


class ResendNotifier(NotificationHandler):
    """Send notifications via Resend API."""
    
    def __init__(self):
        """Initialize Resend notifier."""
        settings = get_settings()
        self.api_key = settings.notify.resend_api_key
        # For Resend, if using a non-verified domain, we must use onboarding@resend.dev
        # or verify the domain at resend.com
        self.email_from = "onboarding@resend.dev"
        self.available = self.api_key is not None
        logger.info(f"ResendNotifier initialized (API Key present: {self.available})")
    
    async def is_configured(self) -> bool:
        """Check if Resend is configured."""
        return self.api_key is not None
    
    async def send(self, notification: Notification) -> bool:
        """
        Send notification via Resend.
        
        Args:
            notification: Notification object
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.debug("Resend API key not configured, skipping")
            return False
            
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        priority_color = "#3b82f6"  # Blue
        if notification.priority == "high":
            priority_color = "#ef4444"  # Red
        elif notification.priority == "medium":
            priority_color = "#ff9f0a"  # Orange

        html_message = notification.message.replace('\n', '<br>')
        status_text = notification.tag.upper() if notification.tag else "NOTIFICATION"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ margin: 0; padding: 0; font-family: sans-serif; background-color: #f3f4f6; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px; border-radius: 8px; margin-top: 40px; }}
                .header {{ border-bottom: 1px solid #e5e7eb; padding-bottom: 20px; margin-bottom: 20px; }}
                .title {{ font-size: 24px; font-weight: bold; color: #111827; }}
                .content {{ font-size: 16px; line-height: 1.6; color: #374151; }}
                .footer {{ margin-top: 40px; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
                .priority {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: bold; color: white; background-color: {priority_color}; text-transform: uppercase; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">DEX COGNITIVE OS • {status_text}</div>
                    <div class="title">{notification.title}</div>
                    <div class="priority">{notification.priority}</div>
                </div>
                <div class="content">
                    {html_message}
                </div>
                <div class="footer">
                    Sent via Dex Personal AI Operator.
                </div>
            </div>
        </body>
        </html>
        """

        payload = {
            "from": f"Dex <{self.email_from}>",
            "to": [self.email_from],
            "subject": notification.title,
            "html": html_body
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status in (200, 201):
                        logger.info(f"Resend notification sent: {notification.title}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Resend notification: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error sending Resend notification: {e}")
            return False
