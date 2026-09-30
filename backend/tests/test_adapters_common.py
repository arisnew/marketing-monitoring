from __future__ import annotations

from datetime import datetime, timezone

from app.adapters.common import parse_datetime, summarize_timestamps


def test_parse_datetime_iso_z():
    dt = parse_datetime("2024-01-15T10:00:00Z")
    assert dt is not None
    assert dt.year == 2024


def test_summarize_timestamps():
    now = datetime.now(timezone.utc)
    count, last, _ = summarize_timestamps([now], 7)
    assert count == 1
    assert last == now
