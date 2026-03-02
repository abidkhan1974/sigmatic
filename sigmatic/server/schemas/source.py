"""Source Pydantic schemas."""

from pydantic import BaseModel


class SourceBase(BaseModel):
    """Base source schema."""

    name: str
    type: str
    schema_adapter: str = "generic"


class SourceCreate(SourceBase):
    """Schema for creating a source."""

    pass


class SourceResponse(SourceBase):
    """Schema for source API responses."""

    source_id: str
    status: str
    trust_score: float

    model_config = {"from_attributes": True}
