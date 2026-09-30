from __future__ import annotations
import httpx

from app.adapters.base import FetchResult, NormalizedMetrics, PlatformAdapter
from app.models.enums import AdapterType, MonitorType


class GenericWebhookAdapter(PlatformAdapter):
    adapter_type = AdapterType.generic_webhook

    def supported_monitor_types(self) -> list[MonitorType]:
        return [MonitorType.custom_webhook, MonitorType.metric_threshold, MonitorType.publish_frequency]

    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        url = adapter_config.get("poll_url")
        if not url:
            raise ValueError("poll_url required in adapter_config")

        headers = (credentials or {}).get("headers", {})
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()

        metrics_payload = payload.get("metrics", payload)
        count = metrics_payload.get("publish_count_in_window")
        metrics = NormalizedMetrics(
            values=metrics_payload if isinstance(metrics_payload, dict) else {"raw": metrics_payload},
            publish_count_in_window=int(count) if count is not None else None,
        )
        return FetchResult(metrics=metrics, evidence={"source": "generic_webhook"})
