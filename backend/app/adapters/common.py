from __future__ import annotations

from datetime import datetime, timedelta, timezone


def parse_datetime(value: str | int | float | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def summarize_timestamps(timestamps: list[datetime], window_days: int) -> tuple[int, datetime | None, list[datetime]]:
    if not timestamps:
        return 0, None, []
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    in_window = [t for t in timestamps if t >= cutoff]
    return len(in_window), max(timestamps), in_window


def require_credential(credentials: dict | None, key: str) -> str:
    if not credentials or not credentials.get(key):
        raise ValueError(f"credentials.{key} required")
    return str(credentials[key])
