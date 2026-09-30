from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import CheckStatus
from app.models.monitor import CheckRun, MetricDaily, MonitorRule

logger = logging.getLogger(__name__)


def aggregate_yesterday(db: Session) -> int:
    """Roll up check runs into metric_daily for the previous UTC day."""
    now = datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - timedelta(days=1)
    day_end = day_start + timedelta(days=1)
    rules = db.query(MonitorRule.id).all()
    written = 0

    for (rule_id,) in rules:
        rows = (
            db.query(CheckRun.status, func.count(CheckRun.id))
            .filter(CheckRun.rule_id == rule_id)
            .filter(CheckRun.started_at >= day_start)
            .filter(CheckRun.started_at < day_end)
            .group_by(CheckRun.status)
            .all()
        )
        if not rows:
            continue
        counts = {status.value: count for status, count in rows}
        last = (
            db.query(CheckRun)
            .filter(CheckRun.rule_id == rule_id)
            .filter(CheckRun.started_at >= day_start)
            .filter(CheckRun.started_at < day_end)
            .order_by(CheckRun.started_at.desc())
            .first()
        )
        stats = {
            "counts": counts,
            "total_runs": sum(counts.values()),
            "last_status": last.status.value if last else None,
        }
        row = db.query(MetricDaily).filter_by(rule_id=rule_id, day=day_start).one_or_none()
        if row is None:
            db.add(MetricDaily(rule_id=rule_id, day=day_start, stats=stats))
        else:
            row.stats = stats
        written += 1

    db.commit()
    logger.info("Daily aggregation: %s rule-day rows for %s", written, day_start.date())
    return written
