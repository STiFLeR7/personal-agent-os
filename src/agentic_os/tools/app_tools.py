"""Application launch tool for Dex."""

from pydantic import Field
from typing import Optional, Any
from agentic_os.tools.base import Tool, ToolInput, ToolOutput
from agentic_os.tools.app_launcher import ApplicationLauncher


class AppLaunchInput(ToolInput):
    """Input for application launcher tool."""
    app_name: str = Field(description="Application name (chrome, whatsapp, discord, etc.)")
    url: Optional[str] = Field(default=None, description="Optional URL to open")


class AppLaunchOutput(ToolOutput):
    """Output from application launcher tool."""
    app_name: str = Field(description="Application that was launched")
    launched: bool = Field(description="Whether launch was successful")
    status: str = Field(description="Status message")


class AppLaunchTool(Tool):
    """Launch applications and URLs."""
    
    def __init__(self):
        super().__init__(
            name="app_launch",
            description="Launch applications like Chrome, WhatsApp, Discord, Teams, Spotify, etc.",
        )
    
    @property
    def input_schema(self) -> type[ToolInput]:
        """Return input schema."""
        return AppLaunchInput
    
    @property
    def output_schema(self) -> type[ToolOutput]:
        """Return output schema."""
        return AppLaunchOutput
    
    async def execute(self, app_name: str, url: Optional[str] = None, **kwargs: Any) -> AppLaunchOutput:
        """
        Execute application launch.
        
        Args:
            app_name: Application name to launch
            url: Optional URL to open with the app
            
        Returns:
            AppLaunchOutput with success status
        """
        try:
            success = await ApplicationLauncher.launch(app_name, url)
            
            if success:
                return AppLaunchOutput(
                    success=True,
                    app_name=app_name,
                    launched=True,
                    status=f"✓ Successfully launched {app_name}",
                    data={
                        "app_name": app_name,
                        "launched": True,
                        "status": f"✓ Successfully launched {app_name}"
                    }
                )
            else:
                supported = ", ".join(ApplicationLauncher.get_supported_apps()[:10])
                return AppLaunchOutput(
                    success=False,
                    app_name=app_name,
                    launched=False,
                    status=f"Failed to launch {app_name}. Supported apps: {supported}...",
                    error=f"Failed to launch {app_name}",
                    data={
                        "app_name": app_name,
                        "launched": False,
                        "status": f"Failed to launch {app_name}"
                    }
                )
                
        except Exception as e:
            return AppLaunchOutput(
                success=False,
                app_name=app_name,
                launched=False,
                status=f"Error launching {app_name}: {str(e)}",
                error=str(e),
                data={
                    "app_name": app_name,
                    "launched": False,
                    "status": f"Error: {str(e)}"
                }
            )
