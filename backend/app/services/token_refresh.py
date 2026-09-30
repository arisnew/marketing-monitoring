from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.adapters.common import parse_datetime
from app.config import get_settings
from app.core.crypto import encrypt_credentials
from app.models.enums import AdapterType
from app.models.platform import Platform

logger = logging.getLogger(__name__)

REFRESH_SOON_DAYS = 7


def _expires_soon(credentials: dict) -> bool:
    expires_at = parse_datetime(credentials.get("expires_at"))
    if expires_at is None:
        return False
    return expires_at <= datetime.now(timezone.utc) + timedelta(days=REFRESH_SOON_DAYS)


async def refresh_meta_access_token(credentials: dict) -> dict:
    settings = get_settings()
    app_id = credentials.get("app_id") or settings.meta_app_id
    app_secret = credentials.get("app_secret") or settings.meta_app_secret
    token = credentials.get("access_token")
    if not all([app_id, app_secret, token]):
        raise ValueError("Meta refresh needs access_token and app_id/app_secret (credentials or env)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://graph.facebook.com/v21.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": token,
            },
        )
        response.raise_for_status()
        payload = response.json()

    updated = {**credentials, "access_token": payload["access_token"]}
    expires_in = payload.get("expires_in")
    if expires_in:
        updated["expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))).isoformat()
    return updated


async def refresh_linkedin_access_token(credentials: dict) -> dict:
    client_id = credentials.get("client_id")
    client_secret = credentials.get("client_secret")
    refresh_token = credentials.get("refresh_token")
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("LinkedIn refresh needs client_id, client_secret, refresh_token")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        payload = response.json()

    updated = {
        **credentials,
        "access_token": payload["access_token"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=int(payload["expires_in"]))).isoformat(),
    }
    if payload.get("refresh_token"):
        updated["refresh_token"] = payload["refresh_token"]
    return updated


async def refresh_credentials_if_needed(
    platform: Platform, credentials: dict | None, *, force: bool = False
) -> tuple[dict | None, bool]:
    if not credentials or not credentials.get("access_token"):
        return credentials, False

    adapter = platform.adapter_type
    should = force or _expires_soon(credentials)
    if not should and not force:
        return credentials, False

    try:
        if adapter in (AdapterType.instagram, AdapterType.facebook):
            updated = await refresh_meta_access_token(credentials)
        elif adapter == AdapterType.linkedin:
            updated = await refresh_linkedin_access_token(credentials)
        else:
            return credentials, False
    except Exception:
        logger.exception("Token refresh failed for platform %s", platform.slug)
        return credentials, False

    return updated, True


def persist_credentials(platform: Platform, credentials: dict) -> None:
    platform.credentials_enc = encrypt_credentials(credentials)


def refresh_due_platform_tokens(db) -> int:
    """Sync job: refresh tokens nearing expiry. Returns count updated."""
    import asyncio

    from app.core.crypto import decrypt_credentials
    from app.models.enums import AdapterType

    refreshable = (
        AdapterType.instagram,
        AdapterType.facebook,
        AdapterType.linkedin,
    )
    updated = 0
    platforms = db.query(Platform).filter(Platform.adapter_type.in_(refreshable)).all()
    for platform in platforms:
        credentials = decrypt_credentials(platform.credentials_enc)
        if not credentials:
            continue
        if not _expires_soon(credentials) and credentials.get("expires_at"):
            continue

        plat, creds = platform, credentials

        async def _one(p=plat, c=creds) -> tuple[dict | None, bool]:
            return await refresh_credentials_if_needed(p, c, force=not c.get("expires_at"))

        new_creds, ok = asyncio.run(_one())
        if ok and new_creds:
            persist_credentials(platform, new_creds)
            updated += 1
    if updated:
        db.commit()
        logger.info("Refreshed credentials for %s platform(s)", updated)
    return updated
