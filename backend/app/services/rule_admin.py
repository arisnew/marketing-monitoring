from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import CheckStatus
from app.models.monitor import CheckRun, MetricDaily, MonitorRule, RuleStatus


def _purge_rule_data(db: Session, rule_id: str) -> None:
    db.query(CheckRun).filter(CheckRun.rule_id == rule_id).delete(synchronize_session=False)
    db.query(MetricDaily).filter(MetricDaily.rule_id == rule_id).delete(synchronize_session=False)
    db.query(RuleStatus).filter(RuleStatus.rule_id == rule_id).delete(synchronize_session=False)


def delete_monitor_rule(db: Session, rule_id: str) -> bool:
    rule = db.get(MonitorRule, rule_id)
    if not rule:
        return False
    _purge_rule_data(db, rule_id)
    db.delete(rule)
    db.commit()
    return True


def delete_platform(db: Session, platform_id: str) -> bool:
    from app.models.platform import Platform

    platform = db.get(Platform, platform_id)
    if not platform:
        return False
    rules = db.query(MonitorRule).filter(MonitorRule.platform_id == platform_id).all()
    for rule in rules:
        _purge_rule_data(db, rule.id)
        db.delete(rule)
    db.delete(platform)
    db.commit()
    return True


def duplicate_monitor_rule(db: Session, rule_id: str) -> MonitorRule | None:
    rule = db.get(MonitorRule, rule_id)
    if not rule:
        return None
    copy = MonitorRule(
        platform_id=rule.platform_id,
        name=f"{rule.name} (copy)",
        monitor_type=rule.monitor_type,
        params=dict(rule.params),
        schedule=dict(rule.schedule),
        thresholds=dict(rule.thresholds),
        enabled=False,
    )
    db.add(copy)
    db.flush()
    db.add(
        RuleStatus(
            rule_id=copy.id,
            status=CheckStatus.unknown,
            next_run_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    db.refresh(copy)
    return copy
