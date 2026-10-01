from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import RequireViewer
from app.config import get_settings
from app.db.session import get_db
from app.models.monitor import MonitorRule
from app.models.user import User

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/status")
def service_status(db: Session = Depends(get_db), _: User = RequireViewer) -> dict:
    settings = get_settings()
    enabled_rules = db.query(MonitorRule).filter(MonitorRule.enabled.is_(True)).count()
    total_rules = db.query(MonitorRule).count()
    return {
        "scheduler_enabled": settings.scheduler_enabled,
        "scheduler_tick_seconds": settings.scheduler_tick_seconds,
        "check_run_retention_days": settings.check_run_retention_days,
        "rules_total": total_rules,
        "rules_enabled": enabled_rules,
    }
