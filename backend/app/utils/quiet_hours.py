"""静默时段判断。"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.strip().split(":", 1)
    return int(hour), int(minute)


def in_quiet_hours(now: datetime | None = None) -> bool:
    tz = ZoneInfo(settings.timezone)
    now = (now or datetime.now(tz=tz)).astimezone(tz)
    start_h, start_m = _parse_hhmm(settings.quiet_hours_start)
    end_h, end_m = _parse_hhmm(settings.quiet_hours_end)
    current = now.hour * 60 + now.minute
    start = start_h * 60 + start_m
    end = end_h * 60 + end_m
    if start <= end:
        return start <= current < end
    return current >= start or current < end


__all__ = ["in_quiet_hours"]
