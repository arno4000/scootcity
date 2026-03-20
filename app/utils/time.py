from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo


# Europe/Zurich timezone
ZURICH_TZ = ZoneInfo("Europe/Zurich")


def timenow() -> datetime:
    """Return timezone-aware Europe/Zurich timestamps for DB defaults."""
    return datetime.now(ZURICH_TZ)


def as_local_time(value: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is timezone-aware in Europe/Zurich timezone."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=ZURICH_TZ)
    return value.astimezone(ZURICH_TZ)
