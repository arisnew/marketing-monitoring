from __future__ import annotations
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

from app.adapters.base import FetchResult, NormalizedMetrics, PlatformAdapter
from app.models.enums import AdapterType, MonitorType


class RssAdapter(PlatformAdapter):
    adapter_type = AdapterType.rss

    def supported_monitor_types(self) -> list[MonitorType]:
        return [MonitorType.publish_frequency, MonitorType.last_activity]

    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        feed_url = adapter_config.get("feed_url") or params.get("feed_url")
        if not feed_url:
            raise ValueError("feed_url required in adapter_config or params")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            parsed = feedparser.parse(response.text)

        entries = parsed.entries or []
        timestamps: list[datetime] = []
        for entry in entries:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                timestamps.append(datetime(*entry.published_parsed[:6], tzinfo=timezone.utc))
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                timestamps.append(datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc))

        window_days = int(params.get("window_days", 7))
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        in_window = [t for t in timestamps if t >= cutoff]
        last_activity = max(timestamps) if timestamps else None

        metrics = NormalizedMetrics(
            values={"entry_count": len(entries), "window_days": window_days},
            last_activity_at=last_activity,
            publish_count_in_window=len(in_window),
        )
        evidence = {
            "feed_title": getattr(parsed.feed, "title", None),
            "sample_titles": [getattr(e, "title", "") for e in entries[:5]],
        }
        return FetchResult(metrics=metrics, evidence=evidence)
