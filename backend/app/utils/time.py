from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_today(tz_name: str = "Asia/Shanghai") -> date:
    return datetime.now(ZoneInfo(tz_name)).date()
