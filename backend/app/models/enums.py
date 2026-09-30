from __future__ import annotations
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    viewer = "viewer"


class AdapterType(str, enum.Enum):
    instagram = "instagram"
    linkedin = "linkedin"
    youtube = "youtube"
    tiktok = "tiktok"
    facebook = "facebook"
    generic_webhook = "generic_webhook"
    rss = "rss"


class MonitorType(str, enum.Enum):
    publish_frequency = "publish_frequency"
    last_activity = "last_activity"
    metric_threshold = "metric_threshold"
    url_health = "url_health"
    custom_webhook = "custom_webhook"


class CheckStatus(str, enum.Enum):
    ok = "ok"
    warning = "warning"
    critical = "critical"
    unknown = "unknown"
