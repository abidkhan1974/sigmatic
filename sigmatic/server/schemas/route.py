"""Routing rule Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Destination sub-schema
# ---------------------------------------------------------------------------

# Destination example:
#   {"type": "webhook", "url": "https://hook.example.com/signals",
#    "method": "POST", "headers": {"Authorization": "Bearer tok"}}

# Filters example:
#   {"symbols": ["AAPL", "TSLA"], "directions": ["long"],
#    "source_ids": ["uuid-1"], "min_quality_score": 0.6}

# RetryPolicy example:
#   {"max_retries": 3, "backoff_seconds": 5}


class RouteCreate(BaseModel):
    """Request body for creating a routing rule."""

    name: str = Field(..., min_length=1, max_length=100)
    destination: dict[str, Any] = Field(
        ...,
        description=(
            'Delivery target. Required key: "url" (str). '
            'Optional keys: "method" (default POST), "headers" (dict).'
        ),
    )
    filters: dict[str, Any] | None = Field(
        None,
        description=(
            "Signal filter criteria. Supported keys: symbols (list[str]), "
            "directions (list[str]), source_ids (list[str]), "
            "min_quality_score (float 0-1)."
        ),
    )
    retry_policy: dict[str, Any] | None = Field(
        None,
        description='Retry config. Keys: "max_retries" (int), "backoff_seconds" (float).',
    )


class RouteUpdate(BaseModel):
    """Request body for updating a routing rule (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    destination: dict[str, Any] | None = None
    filters: dict[str, Any] | None = None
    retry_policy: dict[str, Any] | None = None


class RouteResponse(BaseModel):
    """API response for a routing rule record."""

    route_id: str
    name: str
    destination: dict[str, Any]
    filters: dict[str, Any] | None
    retry_policy: dict[str, Any] | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RouteTestResult(BaseModel):
    """Result of POST /v1/routes/{id}/test."""

    route_id: str
    matched: bool
    reason: str
