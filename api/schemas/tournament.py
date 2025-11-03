"""Tournament schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TournamentOut(BaseModel):
    """Tournament output schema."""

    id: int = Field(..., description="Tournament ID")
    organization_id: int = Field(..., description="Organization ID")
    name: str = Field(..., description="Tournament name")
    description: Optional[str] = Field(None, description="Tournament description")
    is_active: bool = Field(..., description="Whether the tournament is active")
    tracker_enabled: bool = Field(..., description="Whether tracker is enabled")
    created_at: datetime = Field(..., description="Tournament creation timestamp")
    updated_at: datetime = Field(..., description="Tournament last update timestamp")

    class Config:
        from_attributes = True


class TournamentListResponse(BaseModel):
    """Response schema for lists of tournaments."""

    items: list[TournamentOut] = Field(..., description="List of tournament objects")
    count: int = Field(..., description="Total number of tournaments in the result")


class TournamentCreateRequest(BaseModel):
    """Request schema for creating a tournament."""

    name: str = Field(..., min_length=1, max_length=255, description="Tournament name")
    description: Optional[str] = Field(None, description="Tournament description")
    is_active: bool = Field(True, description="Whether the tournament is active")
    tracker_enabled: bool = Field(True, description="Whether tracker is enabled")


class TournamentUpdateRequest(BaseModel):
    """Request schema for updating a tournament."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tournament name")
    description: Optional[str] = Field(None, description="Tournament description")
    is_active: Optional[bool] = Field(None, description="Whether the tournament is active")
    tracker_enabled: Optional[bool] = Field(None, description="Whether tracker is enabled")


class MatchOut(BaseModel):
    """Match output schema."""

    id: int = Field(..., description="Match ID")
    tournament_id: int = Field(..., description="Tournament ID")
    stream_channel_id: Optional[int] = Field(None, description="Stream channel ID")
    scheduled_at: Optional[datetime] = Field(None, description="Match scheduled time")
    checked_in_at: Optional[datetime] = Field(None, description="Check-in time")
    started_at: Optional[datetime] = Field(None, description="Match start time")
    finished_at: Optional[datetime] = Field(None, description="Match finish time")
    confirmed_at: Optional[datetime] = Field(None, description="Match confirmation time")
    comment: Optional[str] = Field(None, description="Match comment")
    title: Optional[str] = Field(None, description="Match title")
    created_at: datetime = Field(..., description="Match creation timestamp")
    updated_at: datetime = Field(..., description="Match last update timestamp")

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Response schema for lists of matches."""

    items: list[MatchOut] = Field(..., description="List of match objects")
    count: int = Field(..., description="Total number of matches in the result")


class MatchCreateRequest(BaseModel):
    """Request schema for creating a match."""

    tournament_id: int = Field(..., description="Tournament ID")
    stream_channel_id: Optional[int] = Field(None, description="Stream channel ID")
    scheduled_at: Optional[datetime] = Field(None, description="Match scheduled time")
    title: Optional[str] = Field(None, max_length=255, description="Match title")
    comment: Optional[str] = Field(None, description="Match comment")
    player_ids: list[int] = Field(default_factory=list, description="List of user IDs to add as players")


class MatchUpdateRequest(BaseModel):
    """Request schema for updating a match."""

    stream_channel_id: Optional[int] = Field(None, description="Stream channel ID")
    scheduled_at: Optional[datetime] = Field(None, description="Match scheduled time")
    checked_in_at: Optional[datetime] = Field(None, description="Check-in time")
    started_at: Optional[datetime] = Field(None, description="Match start time")
    finished_at: Optional[datetime] = Field(None, description="Match finish time")
    confirmed_at: Optional[datetime] = Field(None, description="Match confirmation time")
    title: Optional[str] = Field(None, max_length=255, description="Match title")
    comment: Optional[str] = Field(None, description="Match comment")


class TournamentPlayerOut(BaseModel):
    """Tournament player output schema."""

    id: int = Field(..., description="Registration ID")
    tournament_id: int = Field(..., description="Tournament ID")
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Registration timestamp")

    class Config:
        from_attributes = True


class TournamentPlayerListResponse(BaseModel):
    """Response schema for lists of tournament players."""

    items: list[TournamentPlayerOut] = Field(..., description="List of player registration objects")
    count: int = Field(..., description="Total number of players in the result")


class CrewOut(BaseModel):
    """Crew member output schema."""

    id: int = Field(..., description="Crew signup ID")
    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="Crew role (e.g., 'commentator', 'tracker')")
    match_id: int = Field(..., description="Match ID")
    approved: bool = Field(..., description="Whether the crew signup is approved")
    approved_by_id: Optional[int] = Field(None, description="User ID of the approver")
    created_at: datetime = Field(..., description="Signup timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class CrewApprovalRequest(BaseModel):
    """Request schema for approving/unapproving crew."""

    crew_id: int = Field(..., description="Crew signup ID to approve/unapprove")
