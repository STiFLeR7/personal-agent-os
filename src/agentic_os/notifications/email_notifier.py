"""Email notification handler."""

import asyncio
import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
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
            self.workspace_root = config.workspace_root
        except Exception as e:
            logger.warning(f"Failed to load email config: {e}")
            self.email_from = None
            self.smtp_password = None

    
    async def send(self, notification: Notification) -> bool:
        """
        Send notification via email with a professional structured UI.
        """
        if not await self.is_configured():
            logger.warning("Email notifier not configured")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart("related")
            msg["From"] = f"Dex Cognitive Bot <{self.email_from}>"
            msg["To"] = self.email_from  # Send to self
            msg["Subject"] = notification.title
            
            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)

            # Professional Template (Inspired by Uber/Amazon)
            status_text = notification.tag.upper() if notification.tag else "NOTIFICATION"
            priority_color = "#3b82f6"  # Blue
            if notification.priority == "high":
                priority_color = "#ef4444"  # Red
            
            # Prepare message for HTML
            html_message = notification.message.replace('\n', '<br>')
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #f3f4f6; padding: 40px 20px; }}
                    .card {{ background-color: #ffffff; border-radius: 0; overflow: hidden; }}
                    .header {{ background-color: #000000; padding: 20px 40px; display: flex; align-items: center; }}
                    .header img {{ height: 30px; margin-right: 15px; vertical-align: middle; }}
                    .header span {{ color: #ffffff; font-size: 18px; font-weight: 500; vertical-align: middle; letter-spacing: 0.5px; }}
                    .content {{ padding: 40px; }}
                    .status {{ font-size: 12px; font-weight: 700; color: #6b7280; letter-spacing: 1px; margin-bottom: 15px; text-transform: uppercase; }}
                    .title {{ font-size: 28px; font-weight: 700; color: #111827; margin: 0 0 25px 0; line-height: 1.2; }}
                    .body-text {{ font-size: 16px; line-height: 1.6; color: #374151; margin-bottom: 30px; }}
                    .footer {{ padding: 20px 40px; text-align: left; font-size: 12px; color: #9ca3af; }}
                    .divider {{ height: 1px; background-color: #e5e7eb; margin: 0 40px; }}
                    .priority-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; color: white; background-color: {priority_color}; margin-top: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="card">
                        <div class="header">
                            <img src="cid:dex_logo" alt="Dex">
                            <span>Dex Support</span>
                        </div>
                        <div class="content">
                            <div class="status">{status_text}</div>
                            <h1 class="title">{notification.title}</h1>
                            <div class="body-text">
                                {html_message}
                            </div>
                            <div class="priority-badge">{notification.priority.upper()}</div>
                        </div>
                        <div class="divider"></div>
                        <div class="footer">
                            &copy; 2026 Dex Cognitive OS. Local-first, Privacy-focused.<br>
                            This is an automated message from your personal AI operator.
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text fallback
            text_body = f"Dex: {notification.title}\n\n{notification.message}\n\nPriority: {notification.priority}\nStatus: {status_text}"
            
            msg_alternative.attach(MIMEText(text_body, "plain"))
            msg_alternative.attach(MIMEText(html_body, "html"))
            
            # Embed Logo
            logo_path = Path(self.workspace_root) / "assets" / "dex-icon.png"
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    logo_img = MIMEImage(f.read())
                    logo_img.add_header("Content-ID", "<dex_logo>")
                    logo_img.add_header("Content-Disposition", "inline", filename="dex-icon.png")
                    msg.attach(logo_img)
            
            # Send email in background thread
            await asyncio.to_thread(self._send_smtp, msg)
            
            logger.info(f"Professional HTML Email notification sent: {notification.title}")
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
