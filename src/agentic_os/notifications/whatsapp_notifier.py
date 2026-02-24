"""WhatsApp notification handler via Twilio."""

import asyncio
import logging
from agentic_os.notifications.base import NotificationHandler, Notification
from agentic_os.config import load_config

logger = logging.getLogger(__name__)


class WhatsAppNotifier(NotificationHandler):
    """Send notifications via WhatsApp using Twilio."""
    
    def __init__(self):
        """Initialize WhatsApp notifier from config."""
        try:
            config = load_config()
            self.twilio_auth_token = getattr(config, "twilio_auth_token", None)
            self.twilio_account_sid = getattr(config, "twilio_account_sid", None)
            self.twilio_whatsapp_from = getattr(config, "twilio_whatsapp_from", None)
            self.user_whatsapp_number = getattr(config, "user_whatsapp_number", None)
        except Exception as e:
            logger.warning(f"Failed to load WhatsApp config: {e}")
            self.twilio_auth_token = None
            self.twilio_account_sid = None
    
    async def send(self, notification: Notification) -> bool:
        """
        Send notification via WhatsApp.
        
        Args:
            notification: Notification object
            
        Returns:
            True if sent successfully
        """
        if not await self.is_configured():
            logger.warning("WhatsApp notifier not configured. Set TWILIO credentials in .env")
            return False
        
        try:
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            message_body = f"""🤖 *{notification.title}*

{notification.message}

_Sent by Dex - Your AI Operator_"""
            
            # Send in background thread
            await asyncio.to_thread(
                lambda: client.messages.create(
                    from_=self.twilio_whatsapp_from,
                    to=self.user_whatsapp_number,
                    body=message_body
                )
            )
            
            logger.info(f"WhatsApp notification sent: {notification.title}")
            return True
            
        except ImportError:
            logger.error("Twilio package not installed. Run: pip install twilio")
            return False
        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification: {e}")
            return False
    
    async def is_configured(self) -> bool:
        """Check if WhatsApp notifier is properly configured."""
        return bool(
            self.twilio_auth_token
            and self.twilio_account_sid
            and self.twilio_whatsapp_from
            and self.user_whatsapp_number
        )
