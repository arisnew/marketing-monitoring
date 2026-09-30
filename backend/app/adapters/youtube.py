from __future__ import annotations

import httpx

from app.adapters.base import FetchResult, NormalizedMetrics, PlatformAdapter
from app.adapters.common import parse_datetime, require_credential, summarize_timestamps
from app.models.enums import AdapterType, MonitorType

YT_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeAdapter(PlatformAdapter):
    adapter_type = AdapterType.youtube

    def supported_monitor_types(self) -> list[MonitorType]:
        return [MonitorType.publish_frequency, MonitorType.last_activity, MonitorType.metric_threshold]

    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        channel_id = adapter_config.get("channel_id")
        if not channel_id:
            raise ValueError("adapter_config.channel_id required")
        api_key = None
        access_token = None
        if credentials:
            api_key = credentials.get("api_key")
            access_token = credentials.get("access_token")
        if not api_key and not access_token:
            raise ValueError("credentials.api_key or credentials.access_token required")

        window_days = int(params.get("window_days", 7))
        max_results = min(int(params.get("max_results", 50)), 50)

        headers = {}
        auth_params: dict = {"part": "snippet,statistics,contentDetails", "id": channel_id}
        if api_key:
            auth_params["key"] = api_key
        else:
            headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            ch_resp = await client.get(f"{YT_BASE}/channels", params=auth_params, headers=headers)
            ch_resp.raise_for_status()
            items = ch_resp.json().get("items", [])
            if not items:
                raise ValueError(f"YouTube channel not found: {channel_id}")
            channel = items[0]
            uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})

            pl_params = {
                **auth_params,
                "part": "snippet",
                "playlistId": uploads_id,
                "maxResults": max_results,
            }
            pl_params.pop("id", None)
            pl_resp = await client.get(f"{YT_BASE}/playlistItems", params=pl_params, headers=headers)
            pl_resp.raise_for_status()
            pl_items = pl_resp.json().get("items", [])

        timestamps = []
        titles = []
        for item in pl_items:
            published = item.get("snippet", {}).get("publishedAt")
            ts = parse_datetime(published)
            if ts:
                timestamps.append(ts)
            title = item.get("snippet", {}).get("title")
            if title:
                titles.append(title)

        count, last_activity, _ = summarize_timestamps(timestamps, window_days)
        metrics = NormalizedMetrics(
            values={
                "window_days": window_days,
                "channel_title": snippet.get("title"),
                "subscriber_count": stats.get("subscriberCount"),
                "video_count": stats.get("videoCount"),
            },
            last_activity_at=last_activity,
            publish_count_in_window=count,
        )
        return FetchResult(
            metrics=metrics,
            evidence={"platform": "youtube", "channel_id": channel_id, "sample_titles": titles[:5]},
        )
