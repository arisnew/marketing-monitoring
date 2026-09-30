from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.models.enums import AdapterType, MonitorType


@dataclass
class NormalizedMetrics:
    values: dict = field(default_factory=dict)
    last_activity_at: datetime | None = None
    publish_count_in_window: int | None = None


@dataclass
class FetchResult:
    metrics: NormalizedMetrics
    evidence: dict = field(default_factory=dict)


class PlatformAdapter(ABC):
    adapter_type: AdapterType

    @abstractmethod
    def supported_monitor_types(self) -> list[MonitorType]:
        raise NotImplementedError

    @abstractmethod
    async def fetch(self, adapter_config: dict, credentials: dict | None, params: dict) -> FetchResult:
        raise NotImplementedError
