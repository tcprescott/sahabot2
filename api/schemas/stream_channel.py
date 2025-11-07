"""API schemas for stream channels."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from application.utils.url_validator import validate_url


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

    @field_validator('stream_url')
    @classmethod
    def validate_stream_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate stream URL to prevent XSS and SSRF attacks."""
        if v is None or v.strip() == '':
            return None

        is_valid, error_msg = validate_url(v, allowed_schemes=['http', 'https'], block_private_ips=True)
        if not is_valid:
            raise ValueError(f"Invalid stream URL: {error_msg}")

        return v


class StreamChannelUpdateRequest(BaseModel):
    """Schema for updating a stream channel."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated channel name")
    stream_url: Optional[str] = Field(None, max_length=500, description="Updated stream URL")
    is_active: Optional[bool] = Field(None, description="Updated active status")

    @field_validator('stream_url')
    @classmethod
    def validate_stream_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate stream URL to prevent XSS and SSRF attacks."""
        if v is None or v.strip() == '':
            return None

        is_valid, error_msg = validate_url(v, allowed_schemes=['http', 'https'], block_private_ips=True)
        if not is_valid:
            raise ValueError(f"Invalid stream URL: {error_msg}")

        return v
