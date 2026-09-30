from __future__ import annotations

from app.models.enums import AdapterType
from app.models.platform import Platform
from app.services.platform_fetch import mock_fetch_result


def test_mock_fetch_result():
    platform = Platform(
        slug="demo",
        display_name="Demo",
        adapter_type=AdapterType.youtube,
        adapter_config={"mock": True},
    )
    result = mock_fetch_result(platform, {"window_days": 7, "mock_publish_count": 2})
    assert result.metrics.publish_count_in_window == 2
    assert result.metrics.values.get("mock") is True
