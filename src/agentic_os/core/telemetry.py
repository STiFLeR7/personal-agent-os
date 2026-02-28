"""
Telemetry & Metrics Layer - Observability for Dex.

This module tracks system performance, tool usage, risk distribution, and
LLM token usage to provide insights for the dashboard.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from agentic_os.config import get_settings


class TelemetryEvent(BaseModel):
    """A single telemetry data point."""

    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any]
    task_id: Optional[str] = None


class TelemetryManager:
    """
    Handles logging and aggregation of system metrics.
    """

    def __init__(self, log_path: Optional[Path] = None):
        """Initialize telemetry logging."""
        settings = get_settings()
        self.log_path = log_path or settings.data_dir / "telemetry.jsonl"
        self._ensure_log_exists()

    def _ensure_log_exists(self) -> None:
        """Create telemetry log file if it doesn't exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()

    def log_event(self, event_type: str, data: Dict[str, Any], task_id: Optional[str] = None) -> None:
        """Log an event to the JSONL telemetry file."""
        event = TelemetryEvent(
            event_type=event_type,
            data=data,
            task_id=task_id
        )
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to log telemetry event: {e}")

    def log_task_latency(self, task_id: str, component: str, duration_ms: float) -> None:
        """Track latency for a specific component (e.g., 'planner', 'executor')."""
        self.log_event("latency", {"component": component, "duration_ms": duration_ms}, task_id)

    def log_tool_call(self, task_id: str, tool_name: str, success: bool) -> None:
        """Track tool usage and success rate."""
        self.log_event("tool_call", {"tool": tool_name, "success": success}, task_id)

    def log_risk_assessment(self, task_id: str, risk_level: str, score: float) -> None:
        """Track risk distribution across tasks."""
        self.log_event("risk", {"level": risk_level, "score": score}, task_id)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Aggregate telemetry data for the dashboard.
        """
        summary = {
            "total_tasks": 0,
            "tool_usage": {},
            "avg_latency": {},
            "risk_distribution": {"low": 0, "medium": 0, "high": 0},
            "success_rate": 0,
        }
        
        try:
            events = []
            if self.log_path.exists():
                with open(self.log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))

            total_success = 0
            total_tool_calls = 0
            
            for event in events:
                etype = event["event_type"]
                edata = event["data"]
                
                if etype == "latency":
                    comp = edata["component"]
                    summary["avg_latency"].setdefault(comp, []).append(edata["duration_ms"])
                
                elif etype == "tool_call":
                    total_tool_calls += 1
                    tool = edata["tool"]
                    summary["total_tasks"] += 1 # Rough estimate
                    summary["tool_usage"][tool] = summary["tool_usage"].get(tool, 0) + 1
                    if edata["success"]:
                        total_success += 1
                
                elif etype == "risk":
                    level = edata["level"]
                    summary["risk_distribution"][level] = summary["risk_distribution"].get(level, 0) + 1

            # Finalize averages
            for comp in summary["avg_latency"]:
                vals = summary["avg_latency"][comp]
                summary["avg_latency"][comp] = sum(vals) / len(vals) if vals else 0
            
            summary["success_rate"] = total_success / total_tool_calls if total_tool_calls > 0 else 0
            
        except Exception as e:
            logger.error(f"Failed to generate metrics summary: {e}")
            
        return summary
