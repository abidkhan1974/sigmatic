"""Source Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    """Request body for registering a new signal source."""

    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(webhook|api|internal)$")
    schema_adapter: str = Field("generic", max_length=50)
    config: dict[str, Any] | None = None
    throttle: dict[str, Any] | None = None


class SourceUpdate(BaseModel):
    """Request body for updating a source (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    type: str | None = Field(None, pattern="^(webhook|api|internal)$")
    schema_adapter: str | None = Field(None, max_length=50)
    config: dict[str, Any] | None = None
    throttle: dict[str, Any] | None = None
    trust_score: float | None = Field(None, ge=0.0, le=1.0)


class SourceResponse(BaseModel):
    """API response for a source record."""

    source_id: str
    name: str
    type: str
    schema_adapter: str
    config: dict[str, Any] | None
    throttle: dict[str, Any] | None
    trust_score: float
    stats: dict[str, Any] | None
    status: str
    webhook_token: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
