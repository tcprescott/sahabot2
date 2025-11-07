"""Async Tournament schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AsyncTournamentOut(BaseModel):
    """Async tournament output schema."""

    id: int = Field(..., description="Async tournament ID")
    organization_id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Tournament name")
    description: Optional[str] = Field(None, description="Tournament description")
    is_active: bool = Field(..., description="Whether the tournament is active")
    discord_channel_id: Optional[int] = Field(None, description="Discord channel ID for race creation")
    runs_per_pool: int = Field(..., description="Number of runs allowed per pool")
    created_at: datetime = Field(..., description="Tournament creation timestamp")
    updated_at: datetime = Field(..., description="Tournament last update timestamp")

    class Config:
        from_attributes = True


class AsyncTournamentCreateResponse(BaseModel):
    """Response schema for creating an async tournament."""

    tournament: AsyncTournamentOut = Field(..., description="Created async tournament")
    warnings: List[str] = Field(default_factory=list, description="Permission warnings or validation issues")


class AsyncTournamentListResponse(BaseModel):
    """Response schema for lists of async tournaments."""

    items: list[AsyncTournamentOut] = Field(..., description="List of async tournament objects")
    count: int = Field(..., description="Total number of tournaments in the result")


class AsyncTournamentCreateRequest(BaseModel):
    """Request schema for creating an async tournament."""

    name: str = Field(..., min_length=1, max_length=255, description="Tournament name")
    description: Optional[str] = Field(None, description="Tournament description")
    is_active: bool = Field(True, description="Whether the tournament is active")
    discord_channel_id: Optional[int] = Field(None, description="Discord channel ID for race creation")
    runs_per_pool: int = Field(1, ge=1, le=10, description="Number of runs allowed per pool")


class AsyncTournamentUpdateRequest(BaseModel):
    """Request schema for updating an async tournament."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tournament name")
    description: Optional[str] = Field(None, description="Tournament description")
    is_active: Optional[bool] = Field(None, description="Whether the tournament is active")
    discord_channel_id: Optional[int] = Field(None, description="Discord channel ID for race creation")
    runs_per_pool: Optional[int] = Field(None, ge=1, le=10, description="Number of runs allowed per pool")


class AsyncTournamentPoolOut(BaseModel):
    """Async tournament pool output schema."""

    id: int = Field(..., description="Pool ID")
    tournament_id: int = Field(..., description="Tournament ID")
    name: str = Field(..., description="Pool name")
    description: Optional[str] = Field(None, description="Pool description")
    created_at: datetime = Field(..., description="Pool creation timestamp")

    class Config:
        from_attributes = True


class AsyncTournamentPoolListResponse(BaseModel):
    """Response schema for lists of async tournament pools."""

    items: list[AsyncTournamentPoolOut] = Field(..., description="List of pool objects")
    count: int = Field(..., description="Total number of pools in the result")


class UserBasicInfo(BaseModel):
    """Basic user information for review responses."""

    id: int = Field(..., description="User ID")
    discord_username: str = Field(..., description="Discord username")

    class Config:
        from_attributes = True


class PermalinkBasicInfo(BaseModel):
    """Basic permalink information for review responses."""

    id: int = Field(..., description="Permalink ID")
    url: str = Field(..., description="Permalink URL")
    pool_name: str = Field(..., description="Pool name")


class AsyncTournamentRaceReviewOut(BaseModel):
    """Async tournament race output schema for review purposes."""

    id: int = Field(..., description="Race ID")
    tournament_id: int = Field(..., description="Tournament ID")
    user: UserBasicInfo = Field(..., description="Racer information")
    permalink_id: int = Field(..., description="Permalink ID")
    permalink_url: Optional[str] = Field(None, description="Permalink URL")
    pool_name: Optional[str] = Field(None, description="Pool name")
    status: str = Field(..., description="Race status")
    start_time: Optional[datetime] = Field(None, description="Race start time")
    end_time: Optional[datetime] = Field(None, description="Race end time")
    elapsed_time_formatted: str = Field(..., description="Formatted elapsed time (HH:MM:SS)")
    runner_vod_url: Optional[str] = Field(None, description="Runner's VOD URL")
    runner_notes: Optional[str] = Field(None, description="Runner's notes")
    score: Optional[float] = Field(None, description="Calculated score")
    review_status: str = Field(..., description="Review status")
    reviewed_by: Optional[UserBasicInfo] = Field(None, description="Reviewer information")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes")
    review_requested_by_user: bool = Field(..., description="True if user flagged for review")
    review_request_reason: Optional[str] = Field(None, description="User's reason for requesting review")
    thread_open_time: Optional[datetime] = Field(None, description="Thread open time")
    created_at: datetime = Field(..., description="Race creation timestamp")

    class Config:
        from_attributes = True


class AsyncTournamentRaceReviewListResponse(BaseModel):
    """Response schema for race review queue."""

    items: list[AsyncTournamentRaceReviewOut] = Field(..., description="List of races for review")
    count: int = Field(..., description="Total number of races in the result")


class AsyncTournamentRaceReviewUpdateRequest(BaseModel):
    """Request schema for updating race review."""

    review_status: str = Field(..., pattern="^(pending|accepted|rejected)$", description="Review status")
    reviewer_notes: Optional[str] = Field(None, max_length=10000, description="Reviewer notes")
    elapsed_time_seconds: Optional[int] = Field(None, ge=0, description="Optional elapsed time override in seconds")


class AsyncTournamentRaceUpdateRequest(BaseModel):
    """Request schema for users to update their own race submission."""

    runner_vod_url: Optional[str] = Field(None, max_length=500, description="Runner's VOD URL")
    runner_notes: Optional[str] = Field(None, max_length=10000, description="Runner's notes/comments")
    review_requested_by_user: Optional[bool] = Field(None, description="Flag run for review")
    review_request_reason: Optional[str] = Field(None, max_length=5000, description="Reason for requesting review")
