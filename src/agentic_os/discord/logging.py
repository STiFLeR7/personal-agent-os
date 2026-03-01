"""Discord event logging utilities."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from agentic_os.config import get_settings


def log_discord_event(
    event_type: str,
    data: Dict[str, Any],
    request_id: Optional[str] = None,
) -> None:
    """Write a Discord event to the local JSONL log."""
    settings = get_settings()
    log_path = settings.discord_logs_dir / "discord_events.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "data": data,
    }

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception as exc:
        logger.error(f"Failed to log Discord event: {exc}")
