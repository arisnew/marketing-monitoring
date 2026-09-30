from __future__ import annotations
from app.adapters.base import PlatformAdapter
from app.adapters.linkedin import LinkedInAdapter
from app.adapters.meta_graph import FacebookAdapter, InstagramAdapter
from app.adapters.rss import RssAdapter
from app.adapters.tiktok import TikTokAdapter
from app.adapters.webhook import GenericWebhookAdapter
from app.adapters.youtube import YouTubeAdapter
from app.models.enums import AdapterType

_adapters: dict[AdapterType, PlatformAdapter] = {
    AdapterType.rss: RssAdapter(),
    AdapterType.generic_webhook: GenericWebhookAdapter(),
    AdapterType.instagram: InstagramAdapter(),
    AdapterType.linkedin: LinkedInAdapter(),
    AdapterType.youtube: YouTubeAdapter(),
    AdapterType.tiktok: TikTokAdapter(),
    AdapterType.facebook: FacebookAdapter(),
}


def get_adapter(adapter_type: AdapterType) -> PlatformAdapter:
    adapter = _adapters.get(adapter_type)
    if not adapter:
        raise KeyError(f"No adapter for {adapter_type}")
    return adapter
