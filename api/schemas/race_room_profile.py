"""
API schemas for race room profiles.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RaceRoomProfileBase(BaseModel):
    """Base schema for race room profile."""

    name: str = Field(..., min_length=1, max_length=255, description="Profile name")
    description: Optional[str] = Field(None, description="Profile description")
    start_delay: int = Field(15, ge=10, le=60, description="Race start delay in seconds")
    time_limit: int = Field(24, ge=1, le=72, description="Race time limit in hours")
    streaming_required: bool = Field(False, description="Whether streaming is required")
    auto_start: bool = Field(True, description="Whether to auto-start when ready")
    allow_comments: bool = Field(True, description="Whether to allow race comments")
    hide_comments: bool = Field(False, description="Whether to hide comments until race ends")
    allow_prerace_chat: bool = Field(True, description="Whether to allow pre-race chat")
    allow_midrace_chat: bool = Field(True, description="Whether to allow mid-race chat")
    allow_non_entrant_chat: bool = Field(True, description="Whether to allow non-entrant chat")


class RaceRoomProfileCreate(RaceRoomProfileBase):
    """Schema for creating a race room profile."""

    is_default: bool = Field(False, description="Whether this is the default profile")


class RaceRoomProfileUpdate(BaseModel):
    """Schema for updating a race room profile."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_delay: Optional[int] = Field(None, ge=10, le=60)
    time_limit: Optional[int] = Field(None, ge=1, le=72)
    streaming_required: Optional[bool] = None
    auto_start: Optional[bool] = None
    allow_comments: Optional[bool] = None
    hide_comments: Optional[bool] = None
    allow_prerace_chat: Optional[bool] = None
    allow_midrace_chat: Optional[bool] = None
    allow_non_entrant_chat: Optional[bool] = None
    is_default: Optional[bool] = None


class RaceRoomProfileResponse(RaceRoomProfileBase):
    """Schema for race room profile response."""

    id: int
    organization_id: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RaceRoomProfileListResponse(BaseModel):
    """Schema for list of race room profiles."""

    items: list[RaceRoomProfileResponse]
    count: int
