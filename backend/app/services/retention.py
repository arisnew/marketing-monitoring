from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import engine
from app.models.monitor import CheckRun

logger = logging.getLogger(__name__)


def prune_check_runs(db: Session) -> int:
    days = get_settings().check_run_retention_days
    if days <= 0:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted = db.query(CheckRun).filter(CheckRun.started_at < cutoff).delete(synchronize_session=False)
    db.commit()
    if deleted:
        logger.info("Pruned %s check_run rows older than %s days", deleted, days)
    return deleted


def vacuum_sqlite(db: Session) -> None:
    if not get_settings().database_url.startswith("sqlite"):
        return
    db.commit()
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("VACUUM"))
    logger.info("SQLite VACUUM completed")
