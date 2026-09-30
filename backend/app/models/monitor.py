from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CheckStatus, MonitorType


class MonitorRule(Base):
    __tablename__ = "monitor_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform_id: Mapped[str] = mapped_column(String(36), ForeignKey("platforms.id"), index=True)
    name: Mapped[str] = mapped_column(String(256))
    monitor_type: Mapped[MonitorType] = mapped_column(Enum(MonitorType))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    schedule: Mapped[dict] = mapped_column(JSON, default=dict)
    thresholds: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    platform: Mapped["Platform"] = relationship(back_populates="monitor_rules")
    status: Mapped[Optional["RuleStatus"]] = relationship(back_populates="rule", uselist=False)
    check_runs: Mapped[list["CheckRun"]] = relationship(back_populates="rule")


class RuleStatus(Base):
    __tablename__ = "rule_status"

    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitor_rules.id"), primary_key=True)
    status: Mapped[CheckStatus] = mapped_column(Enum(CheckStatus), default=CheckStatus.unknown)
    last_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_values: Mapped[dict] = mapped_column(JSON, default=dict)
    message: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    rule: Mapped["MonitorRule"] = relationship(back_populates="status")


class CheckRun(Base):
    __tablename__ = "check_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitor_rules.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[CheckStatus] = mapped_column(Enum(CheckStatus))
    evidence_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    rule: Mapped["MonitorRule"] = relationship(back_populates="check_runs")


class MetricDaily(Base):
    __tablename__ = "metric_daily"

    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("monitor_rules.id"), primary_key=True)
    day: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
