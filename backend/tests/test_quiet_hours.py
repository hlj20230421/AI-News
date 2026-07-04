"""静默时段判断单测。"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.quiet_hours import in_quiet_hours


def test_in_quiet_hours_same_day() -> None:
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime(2026, 5, 21, 23, 0, tzinfo=tz)
    assert in_quiet_hours(now) is True


def test_outside_quiet_hours() -> None:
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime(2026, 5, 21, 10, 0, tzinfo=tz)
    assert in_quiet_hours(now) is False
