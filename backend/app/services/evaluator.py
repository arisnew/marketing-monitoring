from __future__ import annotations
from datetime import datetime, timedelta, timezone

from app.adapters.base import NormalizedMetrics
from app.models.enums import CheckStatus, MonitorType


def _parse_interval(schedule: dict) -> timedelta:
    every = schedule.get("every", "6h")
    if isinstance(every, int):
        return timedelta(seconds=every)
    if every.endswith("h"):
        return timedelta(hours=int(every[:-1] or 1))
    if every.endswith("m"):
        return timedelta(minutes=int(every[:-1] or 15))
    return timedelta(hours=6)


def next_run_from_schedule(schedule: dict) -> datetime:
    return datetime.now(timezone.utc) + _parse_interval(schedule)


def evaluate(monitor_type: MonitorType, metrics: NormalizedMetrics, thresholds: dict) -> tuple[CheckStatus, str]:
    if monitor_type == MonitorType.publish_frequency:
        min_count = int(thresholds.get("min_count", thresholds.get("critical_below", 1)))
        warning_below = int(thresholds.get("warning_below", min_count))
        count = metrics.publish_count_in_window
        if count is None:
            return CheckStatus.unknown, "publish_count_in_window not available"
        if count < min_count:
            return CheckStatus.critical, f"Publish count {count} below minimum {min_count}"
        if count < warning_below:
            return CheckStatus.warning, f"Publish count {count} below warning {warning_below}"
        return CheckStatus.ok, f"Publish count {count} OK"

    if monitor_type == MonitorType.metric_threshold:
        field = str(thresholds.get("field", "followers_count"))
        raw = metrics.values.get(field)
        if raw is None:
            return CheckStatus.unknown, f"Metric field '{field}' not available"
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return CheckStatus.unknown, f"Metric field '{field}' is not numeric"
        min_val = thresholds.get("min")
        max_val = thresholds.get("max")
        if min_val is not None and value < float(min_val):
            return CheckStatus.critical, f"{field}={value} below min {min_val}"
        if max_val is not None and value > float(max_val):
            return CheckStatus.critical, f"{field}={value} above max {max_val}"
        return CheckStatus.ok, f"{field}={value} OK"

    if monitor_type == MonitorType.last_activity:
        max_age_hours = int(thresholds.get("max_age_hours", 48))
        warn_hours = int(thresholds.get("warning_hours", max_age_hours // 2))
        if not metrics.last_activity_at:
            return CheckStatus.unknown, "No last activity timestamp"
        age = datetime.now(timezone.utc) - metrics.last_activity_at
        hours = age.total_seconds() / 3600
        if hours > max_age_hours:
            return CheckStatus.critical, f"Last activity {hours:.1f}h ago (max {max_age_hours}h)"
        if hours > warn_hours:
            return CheckStatus.warning, f"Last activity {hours:.1f}h ago (warn {warn_hours}h)"
        return CheckStatus.ok, f"Last activity {hours:.1f}h ago"

    return CheckStatus.unknown, f"Evaluation not implemented for {monitor_type.value}"
