from __future__ import annotations

import httpx

from app.adapters.base import FetchResult, NormalizedMetrics, PlatformAdapter
from app.adapters.common import parse_datetime, require_credential, summarize_timestamps
from app.models.enums import AdapterType, MonitorType

LINKEDIN_POSTS = "https://api.linkedin.com/rest/posts"


class LinkedInAdapter(PlatformAdapter):
    adapter_type = AdapterType.linkedin

    def supported_monitor_types(self) -> list[MonitorType]:
        return [MonitorType.publish_frequency, MonitorType.last_activity]

    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        author = adapter_config.get("author_urn")
        if not author:
            raise ValueError("adapter_config.author_urn required (e.g. urn:li:organization:123)")
        access_token = require_credential(credentials, "access_token")
        window_days = int(params.get("window_days", 7))
        count = min(int(params.get("fetch_count", 50)), 100)
        api_version = adapter_config.get("linkedin_version", "202401")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": api_version,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        query = {"q": "author", "author": author, "count": count, "sortBy": "LAST_MODIFIED"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(LINKEDIN_POSTS, params=query, headers=headers)
            response.raise_for_status()
            payload = response.json()

        timestamps = []
        for element in payload.get("elements", []):
            ts = parse_datetime(
                element.get("publishedAt")
                or element.get("createdAt")
                or element.get("lastModifiedAt")
            )
            if ts:
                timestamps.append(ts)

        pub_count, last_activity, _ = summarize_timestamps(timestamps, window_days)
        metrics = NormalizedMetrics(
            values={"window_days": window_days, "posts_fetched": len(timestamps), "author_urn": author},
            last_activity_at=last_activity,
            publish_count_in_window=pub_count,
        )
        return FetchResult(
            metrics=metrics,
            evidence={"platform": "linkedin", "author_urn": author, "sample_count": len(timestamps)},
        )
