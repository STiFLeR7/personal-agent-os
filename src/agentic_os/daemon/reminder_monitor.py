"""Daemon that monitors reminders and sends notifications."""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from agentic_os.notifications.base import Notification
from agentic_os.notifications.desktop import DesktopNotifier
from agentic_os.notifications.email_notifier import EmailNotifier
from agentic_os.notifications.whatsapp_notifier import WhatsAppNotifier

logger = logging.getLogger(__name__)


class ReminderMonitor:
    """Monitor reminders and send notifications when they're due."""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize reminder monitor.
        
        Args:
            check_interval: Check for due reminders every N seconds (default: 60)
        """
        self.check_interval = check_interval
        self.running = False
        
        # Use same data_dir as reminders tool
        from agentic_os.config import get_settings
        self.reminders_file = get_settings().data_dir / "reminders.json"
        
        # Initialize notification handlers
        self.desktop_notifier = DesktopNotifier()
        self.email_notifier = EmailNotifier()
        self.whatsapp_notifier = WhatsAppNotifier()
        
        # Track sent notifications
        self.sent_notifications = set()
    
    async def start(self):
        """Start the reminder monitor daemon."""
        logger.info("🤖 Dex Reminder Daemon starting...")
        logger.info(f"   Check interval: {self.check_interval} seconds")
        logger.info(f"   Reminders file: {self.reminders_file}")
        
        self.running = True
        
        try:
            while self.running:
                try:
                    await self._check_reminders()
                except Exception as e:
                    logger.error(f"Error in check cycle: {e}", exc_info=True)
                
                # Sleep before next check
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Reminder daemon stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Reminder daemon error: {e}", exc_info=True)
            self.running = False
    
    def stop(self):
        """Stop the reminder monitor daemon."""
        logger.info("Stopping Dex Reminder Daemon...")
        self.running = False
    
    async def _check_reminders(self):
        """Check for due reminders and send notifications."""
        try:
            if not self.reminders_file.exists():
                logger.debug("Reminders file not found, skipping check")
                return
            
            with open(self.reminders_file, "r") as f:
                reminders = json.load(f)
            
            # Get current time in UTC for comparison
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
            logger.debug(f"Checking {len(reminders)} reminders at {now}")
            
            for reminder in reminders:
                reminder_id = reminder.get("id")
                
                # Skip if already notified in this session
                if reminder_id in self.sent_notifications:
                    logger.debug(f"Skipping {reminder_id} - already notified in session")
                    continue
                
                # Skip if not active
                if not reminder.get("is_active", True):
                    logger.debug(f"Skipping {reminder_id} - not active")
                    continue
                
                # Parse scheduled time
                try:
                    scheduled_str = reminder.get("scheduled_time")
                    scheduled = datetime.fromisoformat(scheduled_str)
                    
                    is_due = scheduled <= now
                    
                    logger.debug(f"Reminder {reminder_id}: scheduled={scheduled}, now={now}, due={is_due}")
                    
                    # If time has passed, send notification
                    if is_due:
                        logger.info(f"Sending notification for reminder {reminder_id}: {reminder.get('message')}")
                        await self._send_notification(reminder)
                        self.sent_notifications.add(reminder_id)
                        
                        # Mark as inactive in file
                        reminder["is_active"] = False
                        self._update_reminders(reminders)
                        logger.info(f"Reminder {reminder_id} marked as inactive")
                
                except ValueError as e:
                    logger.error(f"Error parsing scheduled time for {reminder_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing reminder {reminder_id}: {e}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing reminders.json: {e}")
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
    
    async def _send_notification(self, reminder: dict):
        """
        Send notification for a due reminder.
        
        Args:
            reminder: Reminder object
        """
        message = reminder.get("message", "Unnamed reminder")
        priority = reminder.get("priority", "normal")
        reminder_id = reminder.get("id")
        
        notification = Notification(
            title="⏰ Reminder: " + message,
            message=f"Scheduled reminder triggered\nID: {reminder_id}",
            priority=priority,
            tag="reminder"
        )
        
        # Try to send via all configured channels
        results = {
            "desktop": await self.desktop_notifier.send(notification),
            "email": await self.email_notifier.send(notification),
            "whatsapp": await self.whatsapp_notifier.send(notification),
        }
        
        success_channels = [ch for ch, ok in results.items() if ok]
        
        if success_channels:
            logger.info(
                f"✓ Reminder notification sent via {', '.join(success_channels)}: {message}"
            )
        else:
            # If no channels worked, at least log it
            logger.warning(
                f"⚠ Reminder due but no notification channel succeeded: {message}"
            )
    
    def _update_reminders(self, reminders: list):
        """
        Update reminders.json file.
        
        Args:
            reminders: Updated reminders list
        """
        try:
            with open(self.reminders_file, "w") as f:
                json.dump(reminders, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update reminders file: {e}")


async def run_daemon(check_interval: int = 60, daemonize: bool = False):
    """
    Run the reminder daemon.
    
    Args:
        check_interval: Check interval in seconds
        daemonize: If True, run in background (not implemented on Windows)
    """
    monitor = ReminderMonitor(check_interval=check_interval)
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        monitor.stop()
