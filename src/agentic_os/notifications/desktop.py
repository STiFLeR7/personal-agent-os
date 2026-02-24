"""Desktop notification handler for Windows."""

import asyncio
import logging
from agentic_os.notifications.base import NotificationHandler, Notification

logger = logging.getLogger(__name__)


class DesktopNotifier(NotificationHandler):
    """Send notifications as Windows desktop popups."""
    
    def __init__(self):
        """Initialize desktop notifier."""
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Windows notification is available."""
        try:
            import platform
            return platform.system() == "Windows"
        except Exception as e:
            logger.warning(f"Desktop notification check failed: {e}")
            return False
    
    async def send(self, notification: Notification) -> bool:
        """
        Send notification via Windows notification system.
        
        Args:
            notification: Notification object
            
        Returns:
            True if sent successfully
        """
        if not self.available:
            logger.warning("Desktop notifications not available on this system")
            return False
        
        try:
            # Use Windows toast notification
            import subprocess
            
            # PowerShell command to show toast notification
            ps_cmd = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications.ToastNotificationManager, ContentType = WindowsRuntime] > $null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
            
            $toast_xml = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{notification.title}</text>
                        <text id="2">{notification.message}</text>
                    </binding>
                </visual>
            </toast>
            "@
            
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($toast_xml)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Dex - Your AI Operator").Show($toast)
            """
            
            # Run in background
            await asyncio.to_thread(
                lambda: subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True,
                    timeout=5
                )
            )
            
            logger.info(f"Desktop notification sent: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
            return False
    
    async def is_configured(self) -> bool:
        """Check if desktop notification is available."""
        return self.available
