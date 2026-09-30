from __future__ import annotations

import httpx

from app.adapters.base import FetchResult, NormalizedMetrics, PlatformAdapter
from app.adapters.common import parse_datetime, require_credential, summarize_timestamps
from app.models.enums import AdapterType, MonitorType

TIKTOK_VIDEO_LIST = "https://open.tiktokapis.com/v2/video/list/"


class TikTokAdapter(PlatformAdapter):
    adapter_type = AdapterType.tiktok

    def supported_monitor_types(self) -> list[MonitorType]:
        return [MonitorType.publish_frequency, MonitorType.last_activity]

    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        access_token = require_credential(credentials, "access_token")
        window_days = int(params.get("window_days", 7))
        max_count = min(int(params.get("max_count", 20)), 20)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        body = {"max_count": max_count}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TIKTOK_VIDEO_LIST,
                params={"fields": "id,create_time,title"},
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            payload = response.json()

        videos = payload.get("data", {}).get("videos") or []
        timestamps = []
        for video in videos:
            ts = parse_datetime(video.get("create_time"))
            if ts:
                timestamps.append(ts)

        count, last_activity, _ = summarize_timestamps(timestamps, window_days)
        metrics = NormalizedMetrics(
            values={"window_days": window_days, "videos_fetched": len(timestamps)},
            last_activity_at=last_activity,
            publish_count_in_window=count,
        )
        return FetchResult(
            metrics=metrics,
            evidence={"platform": "tiktok", "sample_count": len(timestamps)},
        )
