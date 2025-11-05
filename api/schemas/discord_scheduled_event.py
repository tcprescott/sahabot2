"""Discord scheduled event schemas for API responses."""

from pydantic import BaseModel, Field
from datetime import datetime


class DiscordScheduledEventOut(BaseModel):
    """Discord scheduled event output schema."""

    id: int = Field(..., description="Database record ID")
    organization_id: int = Field(..., description="Organization ID")
    match_id: int = Field(..., description="Match ID")
    scheduled_event_id: int = Field(..., description="Discord scheduled event ID")
    event_slug: str = Field(..., description="Discord event URL slug")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    class Config:
        from_attributes = True


class DiscordScheduledEventListResponse(BaseModel):
    """Response schema for lists of Discord scheduled events."""

    items: list[DiscordScheduledEventOut] = Field(..., description="List of Discord scheduled event objects")
    count: int = Field(..., description="Total number of events in the result")


class SyncEventsRequest(BaseModel):
    """Request schema for syncing Discord events for a tournament."""

    tournament_id: int = Field(..., description="Tournament ID to sync events for")


class SyncEventsResponse(BaseModel):
    """Response schema for event sync operation."""

    success: bool = Field(..., description="Whether the sync was successful")
    stats: dict = Field(..., description="Sync statistics (created, updated, deleted, skipped, errors)")
    message: str = Field(..., description="Human-readable result message")
