"""Base notification handler interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Notification:
    """Notification payload."""
    
    title: str
    message: str
    priority: str = "normal"  # low, normal, high
    tag: Optional[str] = None  # reminder, task, alert, etc.
    action_url: Optional[str] = None


class NotificationHandler(ABC):
    """Abstract base class for notification handlers."""
    
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """
        Send a notification.
        
        Args:
            notification: Notification object
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def is_configured(self) -> bool:
        """
        Check if handler is properly configured.
        
        Returns:
            True if ready to send, False otherwise
        """
        pass
