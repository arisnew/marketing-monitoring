from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireViewer
from app.core.crypto import decrypt_credentials, encrypt_credentials
from app.db.session import get_db
from app.models.platform import Platform
from app.models.user import User
from app.schemas.platform import (
    PlatformCreate,
    PlatformOut,
    PlatformTestRequest,
    PlatformTestResponse,
    PlatformUpdate,
)
from app.services.platform_fetch import fetch_platform
from app.services.rule_admin import delete_platform

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("", response_model=list[PlatformOut])
def list_platforms(db: Session = Depends(get_db), _: User = RequireViewer) -> list[Platform]:
    return db.query(Platform).order_by(Platform.slug).all()


@router.post("", response_model=PlatformOut, status_code=201)
def create_platform(body: PlatformCreate, db: Session = Depends(get_db), _: User = RequireAdmin) -> Platform:
    if db.query(Platform).filter(Platform.slug == body.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    platform = Platform(
        slug=body.slug,
        display_name=body.display_name,
        adapter_type=body.adapter_type,
        adapter_config=body.adapter_config,
        credentials_enc=encrypt_credentials(body.credentials),
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    return platform


@router.patch("/{platform_id}", response_model=PlatformOut)
def update_platform(
    platform_id: str,
    body: PlatformUpdate,
    db: Session = Depends(get_db),
    _: User = RequireAdmin,
) -> Platform:
    platform = db.get(Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    if body.display_name is not None:
        platform.display_name = body.display_name
    if body.adapter_config is not None:
        platform.adapter_config = body.adapter_config
    if body.credentials is not None:
        platform.credentials_enc = encrypt_credentials(body.credentials)
    db.commit()
    db.refresh(platform)
    return platform


@router.get("/{platform_id}/credentials-check")
def credentials_check(platform_id: str, db: Session = Depends(get_db), _: User = RequireAdmin) -> dict:
    platform = db.get(Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    creds = decrypt_credentials(platform.credentials_enc)
    return {"has_credentials": creds is not None}


@router.post("/{platform_id}/test", response_model=PlatformTestResponse)
def test_platform(
    platform_id: str,
    body: PlatformTestRequest,
    db: Session = Depends(get_db),
    _: User = RequireAdmin,
) -> PlatformTestResponse:
    platform = db.get(Platform, platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    async def _run() -> PlatformTestResponse:
        try:
            result, refreshed = await fetch_platform(db, platform, body.params)
            return PlatformTestResponse(
                ok=True,
                mock=bool(platform.adapter_config.get("mock")),
                credential_refreshed=refreshed,
                metrics={
                    "values": result.metrics.values,
                    "last_activity_at": result.metrics.last_activity_at.isoformat()
                    if result.metrics.last_activity_at
                    else None,
                    "publish_count_in_window": result.metrics.publish_count_in_window,
                },
                evidence=result.evidence,
            )
        except Exception as exc:
            return PlatformTestResponse(
                ok=False,
                mock=bool(platform.adapter_config.get("mock")),
                metrics={},
                evidence={},
                error=str(exc),
            )

    return asyncio.run(_run())


@router.delete("/{platform_id}", status_code=204, response_class=Response)
def remove_platform(platform_id: str, db: Session = Depends(get_db), _: User = RequireAdmin) -> Response:
    if not delete_platform(db, platform_id):
        raise HTTPException(status_code=404, detail="Platform not found")
    return Response(status_code=204)
