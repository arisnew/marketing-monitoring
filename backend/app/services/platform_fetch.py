from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.adapters.base import FetchResult, NormalizedMetrics
from app.adapters.registry import get_adapter
from app.core.crypto import decrypt_credentials
from app.models.platform import Platform
from app.services.token_refresh import persist_credentials, refresh_credentials_if_needed


def mock_fetch_result(platform: Platform, params: dict) -> FetchResult:
    window_days = int(params.get("window_days", 7))
    now = datetime.now(timezone.utc)
    return FetchResult(
        metrics=NormalizedMetrics(
            values={
                "mock": True,
                "adapter_type": platform.adapter_type.value,
                "window_days": window_days,
            },
            last_activity_at=now - timedelta(hours=12),
            publish_count_in_window=int(params.get("mock_publish_count", 5)),
        ),
        evidence={"mock": True, "platform_slug": platform.slug},
    )


async def fetch_platform(
    db: Session,
    platform: Platform,
    params: dict,
    *,
    allow_refresh: bool = True,
) -> tuple[FetchResult, bool]:
    """Returns (result, credential_refreshed)."""
    if platform.adapter_config.get("mock"):
        return mock_fetch_result(platform, params), False

    adapter = get_adapter(platform.adapter_type)
    credentials = decrypt_credentials(platform.credentials_enc)
    refreshed = False

    if allow_refresh and credentials:
        credentials, refreshed = await refresh_credentials_if_needed(platform, credentials)
        if refreshed and credentials:
            persist_credentials(platform, credentials)
            db.commit()

    try:
        result = await adapter.fetch(platform.adapter_config, credentials, params)
        return result, refreshed
    except httpx.HTTPStatusError as exc:
        if not allow_refresh or exc.response.status_code not in (401, 403) or not credentials:
            raise
        credentials, refreshed = await refresh_credentials_if_needed(platform, credentials, force=True)
        if not refreshed or not credentials:
            raise
        persist_credentials(platform, credentials)
        db.commit()
        result = await adapter.fetch(platform.adapter_config, credentials, params)
        return result, True
