from __future__ import annotations
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import joinedload

from app.config import get_settings
from app.db.session import SessionLocal
from app.models.monitor import MonitorRule, RuleStatus
from app.services.aggregator import aggregate_yesterday
from app.services.check_runner import run_rule_check
from app.services.token_refresh import refresh_due_platform_tokens

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _process_due_rules() -> None:
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        due = (
            db.query(MonitorRule)
            .join(RuleStatus, RuleStatus.rule_id == MonitorRule.id)
            .options(joinedload(MonitorRule.platform))
            .filter(MonitorRule.enabled.is_(True))
            .filter(RuleStatus.next_run_at.is_not(None))
            .filter(RuleStatus.next_run_at <= now)
            .all()
        )
        for rule in due:
            try:
                run_rule_check(db, rule)
            except Exception:
                logger.exception("Scheduled check failed for rule %s", rule.id)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.scheduler_enabled:
        return None
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _process_due_rules,
        "interval",
        seconds=settings.scheduler_tick_seconds,
        id="due_rules",
        replace_existing=True,
    )

    def _daily_agg() -> None:
        db = SessionLocal()
        try:
            aggregate_yesterday(db)
        except Exception:
            logger.exception("Daily aggregation failed")
        finally:
            db.close()

    _scheduler.add_job(
        _daily_agg,
        "cron",
        hour=1,
        minute=0,
        id="daily_aggregate",
        replace_existing=True,
    )

    def _token_refresh() -> None:
        db = SessionLocal()
        try:
            refresh_due_platform_tokens(db)
        except Exception:
            logger.exception("Token refresh job failed")
        finally:
            db.close()

    _scheduler.add_job(
        _token_refresh,
        "cron",
        hour=2,
        minute=0,
        id="token_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started (tick=%ss)", settings.scheduler_tick_seconds)
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
