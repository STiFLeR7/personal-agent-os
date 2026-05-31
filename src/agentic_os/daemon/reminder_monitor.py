"""Daemon that monitors reminders and sends notifications."""

import asyncio
import json
import sys
from datetime import datetime, timezone, time
from pathlib import Path
from typing import Optional

from loguru import logger
from agentic_os.notifications.base import Notification
from agentic_os.notifications.desktop import DesktopNotifier
from agentic_os.notifications.email_notifier import EmailNotifier
from agentic_os.notifications.whatsapp_notifier import WhatsAppNotifier
from agentic_os.notifications.discord import DiscordNotifier
from agentic_os.notifications.discord_bot_notifier import DiscordBotNotifier
from agentic_os.notifications.resend_notifier import ResendNotifier
from agentic_os.core.telemetry import TelemetryManager

# Remove the old logging.getLogger
# logger = logging.getLogger(__name__)


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
        self.settings = get_settings()
        self.reminders_file = self.settings.data_dir / "reminders.json"
        
        # Initialize notification handlers
        self.desktop_notifier = DesktopNotifier()
        self.email_notifier = EmailNotifier()
        self.whatsapp_notifier = WhatsAppNotifier()
        self.discord_notifier = DiscordNotifier()
        self.discord_bot_notifier = DiscordBotNotifier()
        self.resend_notifier = ResendNotifier()
        
        # Track sent notifications
        self.sent_notifications = set()
        self.last_daily_summary = None
        self.telemetry = TelemetryManager()
    
    async def start(self):
        """Start the reminder monitor daemon."""
        logger.info("🤖 Dex Daemon starting...")
        logger.info(f"   Check interval: {self.check_interval} seconds")
        
        self.running = True
        
        # Start keep-alive loop for Render in a separate task
        asyncio.create_task(self._keep_alive_loop())
        
        try:
            while self.running:
                try:
                    await self._check_reminders()
                    await self._check_daily_summary()
                except Exception as e:
                    logger.error(f"Error in check cycle: {e}")
                
                # Sleep before next check
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            self.running = False

    async def _keep_alive_loop(self):
        """Self-ping loop to prevent Render from spinning down."""
        import aiohttp
        
        url = self.settings.render_external_url
        if not url:
            logger.debug("RENDER_EXTERNAL_URL not set, skipping keep-alive loop")
            return
            
        logger.info(f"🚀 Render Keep-Alive active. Pinging: {url}")
        
        while self.running:
            try:
                # Wait 10 minutes (Render timeout is 15)
                await asyncio.sleep(600)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health") as resp:
                        if resp.status == 200:
                            logger.debug("Pinged self: Stayin' alive! 🕺")
            except Exception as e:
                logger.debug(f"Keep-alive ping failed: {e}")

    async def _check_daily_summary(self):
        """Trigger a daily summary at 8:00 AM IST (02:30 UTC)."""
        from datetime import timezone, time
        now = datetime.now(timezone.utc)
        
        # Target: 02:30 UTC
        target_time = time(2, 30)
        
        if now.time() >= target_time:
            today_date = now.date().isoformat()
            if self.last_daily_summary != today_date:
                logger.info("🌅 Triggering Daily Summary (8:00 AM IST)")
                await self._send_daily_summary()
                self.last_daily_summary = today_date

    async def _send_daily_summary(self):
        """Generate and send a dynamic LLM-generated daily summary."""
        from agentic_os.notifications.base import Notification
        import google.generativeai as genai
        
        logger.info("🌅 Generating Dynamic Daily Summary...")
        
        # 1. Gather Data: Reminders & TODOs
        active_reminders = []
        pending_todos = []
        try:
            # Reminders
            if self.reminders_file.exists():
                with open(self.reminders_file, "r") as f:
                    all_reminders = json.load(f)
                
                now = datetime.now(timezone.utc)
                today = now.date()
                for r in all_reminders:
                    if r.get("is_active"):
                        sched = datetime.fromisoformat(r["scheduled_time"])
                        if sched.date() == today:
                            active_reminders.append(f"- {r['message']} (at {sched.strftime('%H:%M')})")
            
            # TODOs
            todo_file = self.settings.data_dir / "todos.json"
            if todo_file.exists():
                all_todos = json.loads(todo_file.read_text())
                pending_todos = [f"- {t['task']} ({t['priority']} priority)" for t in all_todos if t.get("status") == "pending"]
        except Exception as e:
            logger.error(f"Failed to gather reminders/todos for summary: {e}")

        # 2. Gather Data: Telemetry
        metrics = self.telemetry.get_metrics_summary()
        sys_status = "All nodes operational." if metrics.get("success_rate", 1.0) > 0.8 else "Some nodes experiencing friction."
        
        # 3. LLM Generation
        summary_msg = None
        
        # Try Gemini First
        if self.settings.llm.provider == "google" and self.settings.llm.api_key:
            try:
                genai.configure(api_key=self.settings.llm.api_key)
                # Explicitly use gemini-2.0-flash for best free-tier performance
                model_name = self.settings.llm.model_name or "gemini-2.0-flash"
                model = genai.GenerativeModel(model_name)
                
                reminders_text = "\n".join(active_reminders) if active_reminders else "No specific reminders for today."
                todos_text = "\n".join(pending_todos) if pending_todos else "No pending TODOs."
                
                prompt = f"""
                You are Dex, a high-performance personal AI operator. 
                Write a catchy, professional, and concise body for your "Morning Intel Digest".
                
                IMPORTANT: Do NOT include the words "Morning Intel Digest" or any title at the very beginning, as it will be placed in a separate title field. Start directly with the greeting or the status update.
                
                SYSTEM CONTEXT:
                - Status: {sys_status}
                
                - Active Reminders Today:
                {reminders_text}
                
                - Pending TODOs:
                {todos_text}
                
                - System Metrics:
                  Total Tasks: {metrics.get('total_tasks', 0)}
                  Success Rate: {metrics.get('success_rate', 0):.1%}
                
                FORMATTING RULES:
                - Use professional but engaging tone.
                - Use clean Markdown (no HTML tags like <b>).
                - Keep it under 200 words.
                - Include a "YOUR DAY AT A GLANCE" section.
                - Mention specifically the TODOs that need attention.
                """
                
                response = await model.generate_content_async(prompt)
                summary_msg = response.text.strip()
                logger.info("✅ Summary generated via Gemini.")
            except Exception as e:
                logger.error(f"Gemini summary generation failed: {e}")

        # Try Groq as fallback or alternative
        if not summary_msg and self.settings.llm.groq_api_key:
            try:
                import aiohttp
                logger.info("Attempting to generate summary via Groq engine (fallback)...")
                
                reminders_text = "\n".join(active_reminders) if active_reminders else "No specific reminders for today."
                todos_text = "\n".join(pending_todos) if pending_todos else "No pending TODOs."
                
                prompt = f"""
                You are Dex, a high-performance personal AI operator. 
                Write a catchy, professional, and concise body for your "Morning Intel Digest".
                
                IMPORTANT: Do NOT include the words "Morning Intel Digest" or any title at the very beginning, as it will be placed in a separate title field. Start directly with the greeting or the status update.
                
                SYSTEM CONTEXT:
                - Status: {sys_status}
                - Active Reminders Today: {reminders_text}
                - Pending TODOs: {todos_text}
                
                FORMATTING RULES:
                - Use professional but engaging tone.
                - Use clean Markdown (no HTML tags like <b>).
                - Keep it under 200 words.
                - Include a "YOUR DAY AT A GLANCE" section.
                """
                
                headers = {
                    "Authorization": f"Bearer {self.settings.llm.groq_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            summary_msg = data["choices"][0]["message"]["content"].strip()
                            logger.info("✅ Summary successfully generated via Groq (Llama 3.3).")
                        else:
                            err = await resp.text()
                            logger.error(f"Groq API failed: {resp.status} - {err}")
            except Exception as e:
                logger.error(f"Groq summary generation failed: {e}")

        # Fallback if ALL LLMs fail
        if not summary_msg:
            reminders_text = "\n".join(active_reminders) if active_reminders else "- No reminders scheduled."
            summary_msg = f"""
**SYSTEM STATUS**: {sys_status}
**NODES**: Discord Bot, Background Daemon, Cognitive Core.

**YOUR DAY AT A GLANCE**:
{reminders_text}
- ⚡ Cognitive engine is primed and ready.
- 📧 Mail inbox integration sync complete.

Have a productive morning!
            """

        notification = Notification(
            title="Morning Intel Digest",
            message=summary_msg,
            priority="normal",
            tag="reminders" # Targets #reminders channel
        )
        
        # 4. Delivery: Multi-channel (Discord Bot / Hermes-style)
        recipient = self.settings.notify.email_from
        logger.info(f"Attempting to send Daily Summary to all channels (Recipient: {recipient})...")
        
        # Use our new Hermes-style bot notifier first
        sent_via_bot = await self.discord_bot_notifier.send(notification)
        if not sent_via_bot:
            # Fallback to old webhook if bot token method fails
            await self.discord_notifier.send(notification)
            
        # Resend (Modern)
        if self.settings.notify.resend_api_key:
            logger.info(f"Delivering via Resend to {recipient}")
            await self.resend_notifier.send(notification)
        
        # Legacy SMTP (Fallback)
        if self.settings.notify.email_enabled:
            await self.email_notifier.send(notification)
        
        logger.info("Daily summary cycle complete.")

    
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
            "discord": await self.discord_notifier.send(notification),
            "resend": await self.resend_notifier.send(notification),
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
