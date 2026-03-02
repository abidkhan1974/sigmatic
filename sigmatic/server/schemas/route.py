"""Route Pydantic schemas."""

from typing import Any

from pydantic import BaseModel


class RouteBase(BaseModel):
    """Base routing rule schema."""

    name: str
    destination: dict[str, Any]


class RouteCreate(RouteBase):
    """Schema for creating a routing rule."""

    pass


class RouteResponse(RouteBase):
    """Schema for routing rule API responses."""

    route_id: str
    status: str

    model_config = {"from_attributes": True}
