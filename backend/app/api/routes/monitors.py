from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import RequireAdmin, RequireViewer
from app.db.session import get_db
from app.models.enums import CheckStatus
from app.models.monitor import CheckRun, MetricDaily, MonitorRule, RuleStatus
from app.models.platform import Platform
from app.models.user import User
from app.schemas.monitor import (
    CheckRunOut,
    ComplianceRow,
    DashboardItem,
    MetricDailyOut,
    MonitorRuleCreate,
    MonitorRuleOut,
    MonitorRuleUpdate,
    RuleStatusOut,
)
from app.services.aggregator import aggregate_yesterday
from app.services.analytics import compliance_summary
from app.services.check_runner import run_rule_check
from app.services.rule_admin import delete_monitor_rule, duplicate_monitor_rule

router = APIRouter(prefix="/monitors", tags=["monitors"])


def _ensure_status_row(db: Session, rule: MonitorRule) -> RuleStatus:
    if rule.status is None:
        rule.status = RuleStatus(rule_id=rule.id, status=CheckStatus.unknown)
        db.add(rule.status)
        db.commit()
        db.refresh(rule)
    return rule.status


@router.get("/dashboard", response_model=list[DashboardItem])
def dashboard(db: Session = Depends(get_db), _: User = RequireViewer) -> list[DashboardItem]:
    rules = (
        db.query(MonitorRule)
        .options(joinedload(MonitorRule.platform), joinedload(MonitorRule.status))
        .order_by(MonitorRule.name)
        .all()
    )
    items: list[DashboardItem] = []
    for rule in rules:
        items.append(
            DashboardItem(
                rule=MonitorRuleOut.model_validate(rule),
                status=RuleStatusOut.model_validate(rule.status) if rule.status else None,
                platform_slug=rule.platform.slug,
                platform_display_name=rule.platform.display_name,
            )
        )
    return items


@router.get("/rules", response_model=list[MonitorRuleOut])
def list_rules(db: Session = Depends(get_db), _: User = RequireViewer) -> list[MonitorRule]:
    return db.query(MonitorRule).order_by(MonitorRule.name).all()


@router.post("/rules", response_model=MonitorRuleOut, status_code=201)
def create_rule(body: MonitorRuleCreate, db: Session = Depends(get_db), _: User = RequireAdmin) -> MonitorRule:
    if not db.get(Platform, body.platform_id):
        raise HTTPException(status_code=400, detail="Invalid platform_id")
    rule = MonitorRule(**body.model_dump())
    db.add(rule)
    db.flush()
    db.add(RuleStatus(rule_id=rule.id, status=CheckStatus.unknown, next_run_at=datetime.now(timezone.utc)))
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}", response_model=MonitorRuleOut)
def update_rule(
    rule_id: str, body: MonitorRuleUpdate, db: Session = Depends(get_db), _: User = RequireAdmin
) -> MonitorRule:
    rule = db.get(MonitorRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/rules/{rule_id}/run", response_model=CheckRunOut)
def run_now(rule_id: str, db: Session = Depends(get_db), _: User = RequireAdmin) -> CheckRun:
    rule = db.query(MonitorRule).options(joinedload(MonitorRule.platform)).filter(MonitorRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return run_rule_check(db, rule)


@router.get("/rules/{rule_id}/runs", response_model=list[CheckRunOut])
def list_runs(rule_id: str, db: Session = Depends(get_db), _: User = RequireViewer) -> list[CheckRun]:
    return (
        db.query(CheckRun)
        .filter(CheckRun.rule_id == rule_id)
        .order_by(CheckRun.started_at.desc())
        .limit(50)
        .all()
    )


@router.get("/rules/{rule_id}/metrics/daily", response_model=list[MetricDailyOut])
def list_daily_metrics(rule_id: str, db: Session = Depends(get_db), _: User = RequireViewer) -> list[MetricDaily]:
    return (
        db.query(MetricDaily)
        .filter(MetricDaily.rule_id == rule_id)
        .order_by(MetricDaily.day.desc())
        .limit(30)
        .all()
    )


@router.post("/aggregate/daily", status_code=204, response_class=Response)
def trigger_daily_aggregate(db: Session = Depends(get_db), _: User = RequireAdmin) -> Response:
    aggregate_yesterday(db)
    return Response(status_code=204)


@router.get("/analytics/compliance", response_model=list[ComplianceRow])
def analytics_compliance(
    window_days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    _: User = RequireViewer,
) -> list[ComplianceRow]:
    return [ComplianceRow(**row) for row in compliance_summary(db, window_days)]


@router.get("/rules/{rule_id}/runs/export")
def export_runs_csv(
    rule_id: str,
    db: Session = Depends(get_db),
    _: User = RequireViewer,
) -> StreamingResponse:
    rule = db.get(MonitorRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    runs = (
        db.query(CheckRun)
        .filter(CheckRun.rule_id == rule_id)
        .order_by(CheckRun.started_at.desc())
        .limit(5000)
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["started_at", "finished_at", "status", "error_code", "evidence_summary"])
    for run in runs:
        writer.writerow(
            [
                run.started_at.isoformat() if run.started_at else "",
                run.finished_at.isoformat() if run.finished_at else "",
                run.status.value,
                run.error_code or "",
                str(run.evidence_summary),
            ]
        )
    buffer.seek(0)
    filename = f"check-runs-{rule_id[:8]}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/rules/{rule_id}", status_code=204, response_class=Response)
def delete_rule(rule_id: str, db: Session = Depends(get_db), _: User = RequireAdmin) -> Response:
    if not delete_monitor_rule(db, rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return Response(status_code=204)


@router.post("/rules/{rule_id}/duplicate", response_model=MonitorRuleOut, status_code=201)
def duplicate_rule(rule_id: str, db: Session = Depends(get_db), _: User = RequireAdmin) -> MonitorRule:
    copy = duplicate_monitor_rule(db, rule_id)
    if not copy:
        raise HTTPException(status_code=404, detail="Rule not found")
    return copy
