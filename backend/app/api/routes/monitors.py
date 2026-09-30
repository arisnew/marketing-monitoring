from __future__ import annotations
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from app.api.deps import RequireAdmin, RequireViewer
from app.db.session import get_db
from app.models.enums import CheckStatus
from app.models.monitor import CheckRun, MetricDaily, MonitorRule, RuleStatus
from app.models.platform import Platform
from app.models.user import User
from app.schemas.monitor import (
    CheckRunOut,
    DashboardItem,
    MetricDailyOut,
    MonitorRuleCreate,
    MonitorRuleOut,
    MonitorRuleUpdate,
    RuleStatusOut,
)
from app.services.aggregator import aggregate_yesterday
from app.services.check_runner import run_rule_check

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
