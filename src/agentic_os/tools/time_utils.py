"""
Time and date utilities for Dex.

Helper functions for time parsing, formatting, and timezone handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from zoneinfo import ZoneInfo


def get_current_time(tz: str = "UTC") -> datetime:
    """
    Get current time in specified timezone.

    Args:
        tz: Timezone name (e.g., 'America/New_York', 'UTC')

    Returns:
        Current datetime in specified timezone
    """
    try:
        zone = ZoneInfo(tz)
        return datetime.now(zone)
    except Exception:
        return datetime.now(timezone.utc)


def parse_relative_time(time_str: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse relative time expressions.

    Examples:
        "2 hours from now"
        "tomorrow at 3pm"
        "in 30 minutes"
        "next Monday"

    Args:
        time_str: Time expression
        base_time: Base time to calculate from (defaults to now)

    Returns:
        Parsed datetime or None if unable to parse
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc)

    time_str = time_str.lower().strip()

    # Remove common prefixes
    for prefix in ["in ", "in the ", "at "]:
        if time_str.startswith(prefix):
            time_str = time_str[len(prefix) :]

    # Relative expressions
    if "hour" in time_str:
        try:
            hours = int("".join(filter(str.isdigit, time_str.split("hour")[0])))
            return base_time + timedelta(hours=hours)
        except (ValueError, IndexError):
            pass

    if "minute" in time_str:
        try:
            minutes = int("".join(filter(str.isdigit, time_str.split("minute")[0])))
            return base_time + timedelta(minutes=minutes)
        except (ValueError, IndexError):
            pass

    if "day" in time_str:
        try:
            days = int("".join(filter(str.isdigit, time_str.split("day")[0])))
            return base_time + timedelta(days=days)
        except (ValueError, IndexError):
            pass

    if time_str == "tomorrow":
        return base_time + timedelta(days=1)

    if time_str == "today":
        return base_time

    if time_str == "next week":
        return base_time + timedelta(weeks=1)

    # Time of day (e.g., "3pm", "15:30")
    if any(t in time_str for t in ["am", "pm", ":"]):
        try:
            if "pm" in time_str:
                hour = int(time_str.replace("pm", "").strip())
                if hour != 12:
                    hour += 12
            elif "am" in time_str:
                hour = int(time_str.replace("am", "").strip())
                if hour == 12:
                    hour = 0
            else:  # 24-hour format
                hour = int(time_str.split(":")[0])

            return base_time.replace(hour=hour, minute=0, second=0, microsecond=0)
        except (ValueError, AttributeError):
            pass

    return None


def format_time_since(past_time: datetime) -> str:
    """
    Format time since a past datetime.

    Args:
        past_time: Past datetime

    Returns:
        Human-readable string (e.g., "2 hours ago")
    """
    now = datetime.now(timezone.utc)
    delta = now - past_time

    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return "just now"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif total_seconds < 604800:
        days = total_seconds // 86400
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        weeks = total_seconds // 604800
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"


def format_time_until(future_time: datetime) -> str:
    """
    Format time until a future datetime.

    Args:
        future_time: Future datetime

    Returns:
        Human-readable string (e.g., "in 2 hours")
    """
    now = datetime.now(timezone.utc)
    delta = future_time - now

    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return "now"
    elif total_seconds < 60:
        return "in less than a minute"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"in {minutes} minute{'s' if minutes > 1 else ''}"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"in {hours} hour{'s' if hours > 1 else ''}"
    elif total_seconds < 604800:
        days = total_seconds // 86400
        return f"in {days} day{'s' if days > 1 else ''}"
    else:
        weeks = total_seconds // 604800
        return f"in {weeks} week{'s' if weeks > 1 else ''}"


def is_business_hours(dt: Optional[datetime] = None, tz: str = "UTC") -> bool:
    """
    Check if a time is during business hours (9am-5pm, Mon-Fri).

    Args:
        dt: Datetime to check (defaults to now)
        tz: Timezone for business hours

    Returns:
        True if during business hours
    """
    if dt is None:
        dt = get_current_time(tz)

    return dt.weekday() < 5 and 9 <= dt.hour < 17


def get_greeting(tz: str = "UTC") -> str:
    """
    Get contextual greeting based on time of day.

    Args:
        tz: Timezone for time check

    Returns:
        Greeting string
    """
    now = get_current_time(tz)
    hour = now.hour

    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"
