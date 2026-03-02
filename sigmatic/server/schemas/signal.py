"""Signal Pydantic schemas."""

from pydantic import BaseModel


class SignalBase(BaseModel):
    """Base signal schema."""

    symbol: str
    direction: str


class SignalCreate(SignalBase):
    """Schema for creating a signal."""

    pass


class SignalResponse(SignalBase):
    """Schema for signal API responses."""

    signal_id: str
    status: str

    model_config = {"from_attributes": True}
