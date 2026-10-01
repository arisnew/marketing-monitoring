from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.enums import CheckStatus, MonitorType
from app.models.monitor import CheckRun, MonitorRule


def compliance_summary(db: Session, window_days: int = 7) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    rules = (
        db.query(MonitorRule)
        .options(joinedload(MonitorRule.platform), joinedload(MonitorRule.status))
        .filter(MonitorRule.enabled.is_(True))
        .order_by(MonitorRule.name)
        .all()
    )
    rows: list[dict] = []

    for rule in rules:
        run_stats = (
            db.query(CheckRun.status, func.count(CheckRun.id))
            .filter(CheckRun.rule_id == rule.id, CheckRun.started_at >= since)
            .group_by(CheckRun.status)
            .all()
        )
        counts = {s.value: c for s, c in run_stats}
        total = sum(counts.values())
        ok_count = counts.get(CheckStatus.ok.value, 0)
        compliance_pct = round(100.0 * ok_count / total, 1) if total else None

        target_met: bool | None = None
        target_detail: str | None = None
        if rule.status and rule.monitor_type == MonitorType.publish_frequency:
            min_count = int(rule.thresholds.get("min_count", 1))
            pub = rule.status.last_values.get("publish_count_in_window")
            if pub is not None:
                try:
                    target_met = int(pub) >= min_count
                    target_detail = f"{pub}/{min_count} publish in window"
                except (TypeError, ValueError):
                    pass
        elif rule.status and rule.monitor_type == MonitorType.last_activity:
            target_met = rule.status.status == CheckStatus.ok
            target_detail = rule.status.message

        rows.append(
            {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "monitor_type": rule.monitor_type.value,
                "platform_slug": rule.platform.slug,
                "current_status": rule.status.status.value if rule.status else "unknown",
                "window_days": window_days,
                "runs_total": total,
                "runs_ok": ok_count,
                "compliance_pct": compliance_pct,
                "target_met": target_met,
                "target_detail": target_detail,
            }
        )
    return rows
