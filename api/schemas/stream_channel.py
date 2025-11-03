"""API schemas for stream channels."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StreamChannelOut(BaseModel):
    """Schema for stream channel output."""

    id: int
    organization_id: int
    name: str
    stream_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StreamChannelListResponse(BaseModel):
    """Schema for stream channel list response."""

    items: list[StreamChannelOut]
    count: int


class StreamChannelCreateRequest(BaseModel):
    """Schema for creating a stream channel."""

    name: str = Field(..., min_length=1, max_length=100, description="Channel name")
    stream_url: Optional[str] = Field(None, max_length=500, description="Stream URL (e.g., Twitch channel)")
    is_active: bool = Field(True, description="Whether channel is active")


class StreamChannelUpdateRequest(BaseModel):
    """Schema for updating a stream channel."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated channel name")
    stream_url: Optional[str] = Field(None, max_length=500, description="Updated stream URL")
    is_active: Optional[bool] = Field(None, description="Updated active status")
