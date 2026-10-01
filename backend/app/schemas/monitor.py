from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CheckStatus, MonitorType


class MonitorRuleCreate(BaseModel):
    platform_id: str
    name: str = Field(min_length=1, max_length=256)
    monitor_type: MonitorType
    params: dict = Field(default_factory=dict)
    schedule: dict = Field(default_factory=lambda: {"kind": "interval", "every": "6h"})
    thresholds: dict = Field(default_factory=dict)
    enabled: bool = True


class MonitorRuleUpdate(BaseModel):
    name: str | None = None
    params: dict | None = None
    schedule: dict | None = None
    thresholds: dict | None = None
    enabled: bool | None = None


class MonitorRuleOut(BaseModel):
    id: str
    platform_id: str
    name: str
    monitor_type: MonitorType
    params: dict
    schedule: dict
    thresholds: dict
    enabled: bool

    model_config = {"from_attributes": True}


class RuleStatusOut(BaseModel):
    rule_id: str
    status: CheckStatus
    last_check_at: datetime | None
    next_run_at: datetime | None
    last_values: dict
    message: str | None

    model_config = {"from_attributes": True}


class CheckRunOut(BaseModel):
    id: str
    rule_id: str
    started_at: datetime
    finished_at: datetime | None
    status: CheckStatus
    evidence_summary: dict
    error_code: str | None

    model_config = {"from_attributes": True}


class DashboardItem(BaseModel):
    rule: MonitorRuleOut
    status: RuleStatusOut | None
    platform_slug: str
    platform_display_name: str


class MetricDailyOut(BaseModel):
    rule_id: str
    day: datetime
    stats: dict

    model_config = {"from_attributes": True}


class ComplianceRow(BaseModel):
    rule_id: str
    rule_name: str
    monitor_type: str
    platform_slug: str
    current_status: str
    window_days: int
    runs_total: int
    runs_ok: int
    compliance_pct: float | None
    target_met: bool | None
    target_detail: str | None
