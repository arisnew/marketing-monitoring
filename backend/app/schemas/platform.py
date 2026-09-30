from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import AdapterType


class PlatformCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    adapter_type: AdapterType
    adapter_config: dict = Field(default_factory=dict)
    credentials: dict | None = None


class PlatformUpdate(BaseModel):
    display_name: str | None = None
    adapter_config: dict | None = None
    credentials: dict | None = None


class PlatformOut(BaseModel):
    id: str
    slug: str
    display_name: str
    adapter_type: AdapterType
    adapter_config: dict

    model_config = {"from_attributes": True}


class PlatformTestRequest(BaseModel):
    params: dict = Field(default_factory=lambda: {"window_days": 7})


class PlatformTestResponse(BaseModel):
    ok: bool
    mock: bool = False
    credential_refreshed: bool = False
    metrics: dict
    evidence: dict
    error: str | None = None
