"""Notification system for Dex reminders and task completion."""

from agentic_os.notifications.base import NotificationHandler, Notification
from agentic_os.notifications.desktop import DesktopNotifier
from agentic_os.notifications.email_notifier import EmailNotifier
from agentic_os.notifications.whatsapp_notifier import WhatsAppNotifier

__all__ = [
    "NotificationHandler",
    "Notification",
    "DesktopNotifier",
    "EmailNotifier",
    "WhatsAppNotifier",
]
