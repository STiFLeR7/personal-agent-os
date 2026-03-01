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
            self.email_from = config.notifications.email_from
            self.smtp_server = config.notifications.smtp_server
            self.smtp_port = config.notifications.smtp_port
            self.smtp_password = config.notifications.smtp_password
        except Exception as e:
            logger.warning(f"Failed to load email config: {e}")
            self.email_from = None
            self.smtp_password = None

    
    async def send(self, notification: Notification) -> bool:
        """
        Send notification via email with a catchy HTML UI.
        """
        if not await self.is_configured():
            logger.warning("Email notifier not configured")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email_from
            msg["To"] = self.email_from  # Send to self
            msg["Subject"] = f"✨ Dex: {notification.title}"
            
            # Catchy HTML Template
            html_body = f"""
            <html>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #e2e8f0;">
                <div style="max-width: 600px; margin: 20px auto; background-color: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);">
                    <!-- Header -->
                    <div style="background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%); padding: 20px; text-align: center;">
                        <h1 style="margin: 0; color: white; font-size: 24px; letter-spacing: 1px;">DEX COGNITIVE BOT</h1>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 30px;">
                        <h2 style="color: #3b82f6; margin-top: 0;">{notification.title}</h2>
                        <div style="line-height: 1.6; color: #94a3b8; font-size: 16px; background-color: #0f172a; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                            {notification.message.replace('\\n', '<br>')}
                        </div>
                        
                        <div style="margin-top: 30px; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #334155; padding-top: 20px;">
                            <div>
                                <span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; background-color: #3b82f6; color: white; text-transform: uppercase;">
                                    {notification.priority}
                                </span>
                            </div>
                            <div style="font-size: 12px; color: #64748b;">
                                Ref: {notification.tag or 'System'}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #0f172a; padding: 15px; text-align: center; font-size: 11px; color: #475569;">
                        Processed autonomously by your personal assistant.<br>
                        Local-First • Privacy-Focused • Intelligent
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text fallback
            text_body = f"Dex: {notification.title}\n\n{notification.message}\n\nPriority: {notification.priority}"
            
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email in background thread
            await asyncio.to_thread(self._send_smtp, msg)
            
            logger.info(f"HTML Email notification sent: {notification.title}")
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
