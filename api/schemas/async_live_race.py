"""Async Live Race schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AsyncLiveRaceOut(BaseModel):
    """Async live race output schema."""

    id: int = Field(..., description="Live race ID")
    tournament_id: int = Field(..., description="Tournament ID")
    pool_id: int = Field(..., description="Pool ID")
    pool_name: Optional[str] = Field(None, description="Pool name")
    permalink_id: Optional[int] = Field(None, description="Permalink ID")
    permalink_url: Optional[str] = Field(None, description="Permalink URL")
    episode_id: Optional[int] = Field(None, description="SpeedGaming episode ID")
    scheduled_at: Optional[datetime] = Field(
        None, description="Scheduled race start time"
    )
    match_title: Optional[str] = Field(None, description="Match title/display name")
    racetime_slug: Optional[str] = Field(None, description="RaceTime.gg race slug")
    racetime_url: Optional[str] = Field(None, description="RaceTime.gg race URL")
    racetime_goal: Optional[str] = Field(None, description="RaceTime.gg race goal")
    room_open_time: Optional[datetime] = Field(None, description="Time room was opened")
    race_room_profile_id: Optional[int] = Field(
        None, description="Race room profile ID"
    )
    status: str = Field(
        ...,
        description="Race status (scheduled/pending/in_progress/finished/cancelled)",
    )
    participant_count: int = Field(0, description="Number of participants")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class AsyncLiveRaceListResponse(BaseModel):
    """Response schema for lists of async live races."""

    items: list[AsyncLiveRaceOut] = Field(..., description="List of live race objects")
    count: int = Field(..., description="Total number of races in the result")


class AsyncLiveRaceCreateRequest(BaseModel):
    """Request schema for creating an async live race."""

    tournament_id: int = Field(..., description="Tournament ID")
    pool_id: int = Field(..., description="Pool ID")
    scheduled_at: datetime = Field(..., description="Scheduled race start time")
    match_title: Optional[str] = Field(
        None, max_length=200, description="Match title/display name"
    )
    permalink_id: Optional[int] = Field(
        None, description="Specific permalink/seed to use"
    )
    episode_id: Optional[int] = Field(None, description="SpeedGaming episode ID")
    race_room_profile_id: Optional[int] = Field(
        None, description="Race room profile override"
    )


class AsyncLiveRaceUpdateRequest(BaseModel):
    """Request schema for updating an async live race."""

    scheduled_at: Optional[datetime] = Field(
        None, description="Scheduled race start time"
    )
    match_title: Optional[str] = Field(
        None, max_length=200, description="Match title/display name"
    )
    permalink_id: Optional[int] = Field(
        None, description="Specific permalink/seed to use"
    )
    episode_id: Optional[int] = Field(None, description="SpeedGaming episode ID")
    race_room_profile_id: Optional[int] = Field(
        None, description="Race room profile override"
    )


class EligibleParticipantOut(BaseModel):
    """Eligible participant output schema."""

    user_id: int = Field(..., description="User ID")
    discord_username: str = Field(..., description="Discord username")
    is_eligible: bool = Field(..., description="Whether user is eligible")
    reason: Optional[str] = Field(None, description="Reason if not eligible")


class EligibleParticipantsResponse(BaseModel):
    """Response schema for eligible participants list."""

    items: list[EligibleParticipantOut] = Field(
        ..., description="List of participants with eligibility info"
    )
    count: int = Field(..., description="Total number of participants")
    eligible_count: int = Field(..., description="Number of eligible participants")
