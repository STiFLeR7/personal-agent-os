"""
Gmail and email integration tools (Phase 3 - Implementation).

Framework for Gmail API integration and direct SMTP composition.
"""

from typing import Any, Optional, List
import asyncio
from pydantic import Field
from loguru import logger

from agentic_os.tools.base import Tool, ToolInput, ToolOutput
from agentic_os.notifications.email_notifier import EmailNotifier
from agentic_os.notifications.base import Notification


class EmailComposeInput(ToolInput):
    """Input for composing an email."""

    recipient: Optional[str] = Field(default=None, description="Primary recipient email address")
    recipients: Optional[List[str]] = Field(default=None, description="List of recipient email addresses")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body")


class EmailComposeOutput(ToolOutput):
    """Output from email composition."""

    draft_id: Optional[str] = Field(default=None, description="Draft message ID")
    sent_to: Optional[str] = Field(default=None, description="Recipient email address")


class EmailComposeTool(Tool):
    """Tool for composing and sending emails via SMTP."""

    def __init__(self):
        """Initialize the email compose tool."""
        super().__init__(
            name="email_compose",
            description="Compose and send an email via your configured SMTP server.",
        )
        self.notifier = EmailNotifier()

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return EmailComposeInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return EmailComposeOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """Execute the email composition and sending."""
        # Robustly handle both 'recipient' and 'recipients' from LLM
        recipient = kwargs.get("recipient")
        recipients = kwargs.get("recipients")
        
        target_recipient = ""
        if recipient and isinstance(recipient, str):
            target_recipient = recipient.strip()
        elif recipients:
            if isinstance(recipients, list) and len(recipients) > 0:
                target_recipient = str(recipients[0]).strip()
            elif isinstance(recipients, str):
                target_recipient = recipients.strip()

        subject = kwargs.get("subject", "No Subject").strip()
        body = kwargs.get("body", "").strip()

        if not target_recipient or not body:
            return EmailComposeOutput(
                success=False,
                error="Recipient (or recipients[0]) and body are required",
            )

        try:
            # Check if notifier is configured
            if not await self.notifier.is_configured():
                return EmailComposeOutput(
                    success=False,
                    error="Email SMTP not configured in .env. Need NOTIFY_EMAIL_FROM and NOTIFY_SMTP_PASSWORD.",
                )

            # Construct notification object to reuse EmailNotifier logic
            notification = Notification(
                title=subject,
                message=body,
                priority="normal",
                tag="email_outbound"
            )

            # Send email
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from agentic_os.config import get_settings
            
            settings = get_settings()
            email_from = settings.notifications.email_from
            password = settings.notifications.smtp_password
            server_addr = settings.notifications.smtp_server
            port = settings.notifications.smtp_port

            msg = MIMEMultipart()
            msg["From"] = email_from
            msg["To"] = target_recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            def _send():
                with smtplib.SMTP(server_addr, port) as server:
                    server.starttls()
                    server.login(email_from, password)
                    server.send_message(msg)

            await asyncio.to_thread(_send)

            logger.info(f"Email sent successfully to {target_recipient}")
            return EmailComposeOutput(
                success=True,
                sent_to=target_recipient,
                data={"recipient": target_recipient, "subject": subject}
            )

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return EmailComposeOutput(
                success=False,
                error=f"Email delivery failed: {str(e)}",
            )



class BrowserOpenInput(ToolInput):
    """Input for opening browser and navigating."""

    url: str = Field(description="URL to navigate to")
    new_tab: bool = Field(default=False, description="Open in new tab")


class BrowserOpenOutput(ToolOutput):
    """Output from browser operation."""

    session_id: Optional[str] = Field(default=None, description="Browser session ID")


class BrowserOpenTool(Tool):
    """Tool for browser automation (placeholder for Selenium integration)."""

    def __init__(self):
        """Initialize the browser tool."""
        super().__init__(
            name="browser_open",
            description="Open and navigate browser (Selenium integration coming in v0.3)",
        )

    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return BrowserOpenInput

    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return BrowserOpenOutput

    async def execute(self, **kwargs: Any) -> ToolOutput:
        """Placeholder implementation."""
        return BrowserOpenOutput(
            success=False,
            error="Browser automation coming in v0.3. Use ShellCommand tool for now: 'start https://...'",
            session_id=None,
        )
