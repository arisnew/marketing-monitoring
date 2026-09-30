from __future__ import annotations

from typing import Any

import httpx

from app.adapters.base import FetchResult, NormalizedMetrics, PlatformAdapter
from app.adapters.common import parse_datetime, require_credential, summarize_timestamps
from app.models.enums import AdapterType, MonitorType

GRAPH_BASE = "https://graph.facebook.com/v21.0"


async def _fetch_timestamps(
    client: httpx.AsyncClient,
    access_token: str,
    edge: str,
    time_field: str,
    max_pages: int,
) -> list:
    from datetime import datetime

    url = f"{GRAPH_BASE}/{edge.lstrip('/')}"
    params: dict[str, Any] = {"access_token": access_token, "limit": 25, "fields": f"id,{time_field}"}
    timestamps: list[datetime] = []
    pages = 0
    while url and pages < max_pages:
        response = await client.get(url, params=params if pages == 0 else None)
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("data", []):
            ts = parse_datetime(item.get(time_field))
            if ts:
                timestamps.append(ts)
        url = payload.get("paging", {}).get("next")
        params = None
        pages += 1
    return timestamps


class InstagramAdapter(PlatformAdapter):
    adapter_type = AdapterType.instagram

    def supported_monitor_types(self) -> list[MonitorType]:
        return [MonitorType.publish_frequency, MonitorType.last_activity, MonitorType.metric_threshold]

    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        ig_user_id = adapter_config.get("ig_user_id")
        if not ig_user_id:
            raise ValueError("adapter_config.ig_user_id required (Instagram Business/Creator ID)")
        access_token = require_credential(credentials, "access_token")
        window_days = int(params.get("window_days", 7))
        max_pages = int(params.get("max_pages", 2))

        async with httpx.AsyncClient(timeout=30.0) as client:
            timestamps = await _fetch_timestamps(
                client, access_token, f"{ig_user_id}/media", "timestamp", max_pages
            )
            profile_values: dict = {}
            if params.get("include_profile_metrics"):
                resp = await client.get(
                    f"{GRAPH_BASE}/{ig_user_id}",
                    params={
                        "access_token": access_token,
                        "fields": "followers_count,media_count,username",
                    },
                )
                resp.raise_for_status()
                profile_values = resp.json()

        count, last_activity, _ = summarize_timestamps(timestamps, window_days)
        metrics = NormalizedMetrics(
            values={
                "window_days": window_days,
                "media_fetched": len(timestamps),
                **profile_values,
            },
            last_activity_at=last_activity,
            publish_count_in_window=count,
        )
        return FetchResult(
            metrics=metrics,
            evidence={"platform": "instagram", "ig_user_id": ig_user_id, "sample_count": len(timestamps)},
        )


class FacebookAdapter(PlatformAdapter):
    adapter_type = AdapterType.facebook

    def supported_monitor_types(self) -> list[MonitorType]:
        return [MonitorType.publish_frequency, MonitorType.last_activity]

    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        page_id = adapter_config.get("page_id")
        if not page_id:
            raise ValueError("adapter_config.page_id required")
        access_token = require_credential(credentials, "access_token")
        window_days = int(params.get("window_days", 7))
        max_pages = int(params.get("max_pages", 2))

        async with httpx.AsyncClient(timeout=30.0) as client:
            timestamps = await _fetch_timestamps(
                client, access_token, f"{page_id}/posts", "created_time", max_pages
            )

        count, last_activity, _ = summarize_timestamps(timestamps, window_days)
        metrics = NormalizedMetrics(
            values={"window_days": window_days, "posts_fetched": len(timestamps)},
            last_activity_at=last_activity,
            publish_count_in_window=count,
        )
        return FetchResult(
            metrics=metrics,
            evidence={"platform": "facebook", "page_id": page_id, "sample_count": len(timestamps)},
        )
