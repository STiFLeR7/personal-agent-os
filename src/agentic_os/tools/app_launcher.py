"""Extended application launcher for Windows."""

import asyncio
import logging
import subprocess
import platform
from pathlib import Path

logger = logging.getLogger(__name__)


class ApplicationLauncher:
    """Launch various applications on Windows."""
    
    # Application mappings - app name -> command / executable
    APP_MAPPINGS = {
        # Web browsers
        "chrome": "start chrome",
        "chromium": "start chrome",
        "edge": "start msedge",
        "firefox": "start firefox",
        "brave": "start brave",
        
        # Chat & Communication
        "whatsapp": "start whatsapp:",
        "telegram": "start telegram:",
        "discord": "start discord",
        "teams": "start teams",
        "slack": "start slack",
        "messenger": "start fb-messenger:",
        "signal": "start signal",
        
        # System
        "settings": "start ms-settings:",
        "calculator": "start calc",
        "notepad": "start notepad",
        "explorer": "start explorer",
        "paint": "start mspaint",
        "word": "start winword",
        "excel": "start excel",
        "powerpoint": "start powerpnt",
        
        # Development
        "vscode": "start code",
        "visualstudio": "start devenv",
        "cmd": "start cmd",
        "powershell": "start powershell",
        
        # Media
        "spotify": "start spotify",
        "youtube": "start https://youtube.com",
        "netflix": "start https://netflix.com",
        "vlc": "start vlc",
    }
    
    @staticmethod
    async def launch(app_name: str, url: str = None) -> bool:
        """
        Launch an application by name.
        
        Args:
            app_name: Application name or custom URL
            url: Optional URL to open with the app
            
        Returns:
            True if launched successfully, False otherwise
        """
        if platform.system() != "Windows":
            logger.error("Application launcher only supports Windows")
            return False
        
        try:
            app_name_lower = app_name.lower().strip()
            
            # Check if it's a URL
            if app_name_lower.startswith("http://") or app_name_lower.startswith("https://"):
                command = f"start {app_name_lower}"
            # Check if app is in mappings
            elif app_name_lower in ApplicationLauncher.APP_MAPPINGS:
                command = ApplicationLauncher.APP_MAPPINGS[app_name_lower]
                if url:
                    command += f" {url}"
            # Otherwise try to launch directly
            else:
                command = f"start {app_name_lower}"
                if url:
                    command += f" {url}"
            
            # Execute in background
            await asyncio.to_thread(
                lambda: subprocess.Popen(command, shell=True)
            )
            
            logger.info(f"✓ Launched: {app_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch {app_name}: {e}")
            return False
    
    @staticmethod
    async def launch_whatsapp_chat(phone_number: str = None) -> bool:
        """
        Launch WhatsApp and optionally open a chat with a number.
        
        Args:
            phone_number: Optional phone number (with country code, no +)
            
        Returns:
            True if successful
        """
        try:
            if phone_number:
                # Format: https://wa.me/1234567890
                command = f"start https://wa.me/{phone_number}"
            else:
                command = "start whatsapp:"
            
            await asyncio.to_thread(
                lambda: subprocess.Popen(command, shell=True)
            )
            
            logger.info(f"✓ Opened WhatsApp: {phone_number or 'main app'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch WhatsApp: {e}")
            return False
    
    @staticmethod
    async def launch_url(url: str) -> bool:
        """
        Launch a URL in default browser.
        
        Args:
            url: URL to open
            
        Returns:
            True if successful
        """
        try:
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            
            command = f"start {url}"
            
            await asyncio.to_thread(
                lambda: subprocess.Popen(command, shell=True)
            )
            
            logger.info(f"✓ Opened URL: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch URL: {e}")
            return False
    
    @staticmethod
    def get_supported_apps() -> list:
        """Get list of supported applications."""
        return list(ApplicationLauncher.APP_MAPPINGS.keys())
