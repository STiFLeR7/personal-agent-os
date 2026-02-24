"""Email notification handler."""

import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from agentic_os.notifications.base import NotificationHandler, Notification
from agentic_os.config import load_config

logger = logging.getLogger(__name__)


class EmailNotifier(NotificationHandler):
    """Send notifications via email."""
    
    def __init__(self):
        """Initialize email notifier from config."""
        try:
            config = load_config()
            self.email_from = getattr(config, "email_from", None)
            self.smtp_server = getattr(config, "smtp_server", "smtp.gmail.com")
            self.smtp_port = getattr(config, "smtp_port", 587)
            self.smtp_password = getattr(config, "smtp_password", None)
        except Exception as e:
            logger.warning(f"Failed to load email config: {e}")
            self.email_from = None
            self.smtp_password = None
    
    async def send(self, notification: Notification) -> bool:
        """
        Send notification via email.
        
        Args:
            notification: Notification object
            
        Returns:
            True if sent successfully
        """
        if not await self.is_configured():
            logger.warning("Email notifier not configured")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.email_from
            msg["To"] = self.email_from  # Send to self
            msg["Subject"] = f"🤖 Dex: {notification.title}"
            
            body = f"""
Dex - Your Personal AI Operator

{notification.title}

{notification.message}

---
Priority: {notification.priority.upper()}
Type: {notification.tag or 'Notification'}

This is an automated message from Dex.
            """.strip()
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email in background thread
            await asyncio.to_thread(self._send_smtp, msg)
            
            logger.info(f"Email notification sent: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_smtp(self, msg):
        """Send email via SMTP."""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_from, self.smtp_password)
            server.send_message(msg)
    
    async def is_configured(self) -> bool:
        """Check if email notifier is properly configured."""
        return bool(self.email_from and self.smtp_password)
