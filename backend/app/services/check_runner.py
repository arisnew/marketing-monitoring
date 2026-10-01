from __future__ import annotations
import asyncio
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import CheckStatus
from app.models.monitor import CheckRun, MonitorRule, RuleStatus
from app.services.evaluator import evaluate, next_run_from_schedule
from app.services.platform_fetch import fetch_platform
from app.services.notifier import notify_status_change


def run_rule_check(db: Session, rule: MonitorRule) -> CheckRun:
    return asyncio.run(_run_rule_check_async(db, rule))


async def _run_rule_check_async(db: Session, rule: MonitorRule) -> CheckRun:
    started = datetime.now(timezone.utc)
    run = CheckRun(rule_id=rule.id, started_at=started, status=CheckStatus.unknown)
    db.add(run)

    previous = CheckStatus.unknown
    status_row = db.get(RuleStatus, rule.id)
    if status_row:
        previous = status_row.status

    try:
        result, _refreshed = await fetch_platform(db, rule.platform, rule.params)
        status, message = evaluate(rule.monitor_type, result.metrics, rule.thresholds)
        run.status = status
        run.evidence_summary = result.evidence
        run.finished_at = datetime.now(timezone.utc)

        if status_row is None:
            status_row = RuleStatus(rule_id=rule.id)
            db.add(status_row)
        status_row.status = status
        status_row.last_check_at = run.finished_at
        status_row.next_run_at = next_run_from_schedule(rule.schedule)
        last_values = dict(result.metrics.values)
        if result.metrics.publish_count_in_window is not None:
            last_values["publish_count_in_window"] = result.metrics.publish_count_in_window
        if result.metrics.last_activity_at is not None:
            last_values["last_activity_at"] = result.metrics.last_activity_at.isoformat()
        status_row.last_values = last_values
        status_row.message = message

        notify_email = rule.params.get("notify_email")
        notify_webhook = rule.params.get("notify_webhook_url")
        await notify_status_change(rule, previous, status, message, notify_webhook, notify_email)
    except NotImplementedError as exc:
        run.status = CheckStatus.unknown
        run.error_code = "adapter_not_implemented"
        run.evidence_summary = {"error": str(exc)}
        run.finished_at = datetime.now(timezone.utc)
    except Exception as exc:
        run.status = CheckStatus.critical
        run.error_code = "fetch_failed"
        run.evidence_summary = {"error": str(exc)}
        run.finished_at = datetime.now(timezone.utc)
        if status_row:
            status_row.status = CheckStatus.critical
            status_row.message = str(exc)
            status_row.last_check_at = run.finished_at

    db.commit()
    db.refresh(run)
    return run
