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
    speedgaming_enabled: bool = Field(
        ..., description="Whether SpeedGaming integration is enabled"
    )
    speedgaming_event_slug: Optional[str] = Field(
        None, description="SpeedGaming event slug"
    )
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
    speedgaming_enabled: bool = Field(
        False, description="Enable SpeedGaming integration (makes schedule read-only)"
    )
    speedgaming_event_slug: Optional[str] = Field(
        None,
        max_length=255,
        description="SpeedGaming event slug (required if speedgaming_enabled=True)",
    )


class TournamentUpdateRequest(BaseModel):
    """Request schema for updating a tournament."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Tournament name"
    )
    description: Optional[str] = Field(None, description="Tournament description")
    is_active: Optional[bool] = Field(
        None, description="Whether the tournament is active"
    )
    tracker_enabled: Optional[bool] = Field(
        None, description="Whether tracker is enabled"
    )
    speedgaming_enabled: Optional[bool] = Field(
        None, description="Enable SpeedGaming integration (makes schedule read-only)"
    )
    speedgaming_event_slug: Optional[str] = Field(
        None,
        max_length=255,
        description="SpeedGaming event slug (required if speedgaming_enabled=True)",
    )


class MatchOut(BaseModel):
    """Match output schema."""

    id: int = Field(..., description="Match ID")
    tournament_id: int = Field(..., description="Tournament ID")
    stream_channel_id: Optional[int] = Field(None, description="Stream channel ID")
    scheduled_at: Optional[datetime] = Field(None, description="Match scheduled time")
    checked_in_at: Optional[datetime] = Field(None, description="Check-in time")
    started_at: Optional[datetime] = Field(None, description="Match start time")
    finished_at: Optional[datetime] = Field(None, description="Match finish time")
    confirmed_at: Optional[datetime] = Field(
        None, description="Match confirmation time"
    )
    comment: Optional[str] = Field(None, description="Match comment")
    title: Optional[str] = Field(None, description="Match title")
    speedgaming_episode_id: Optional[int] = Field(
        None, description="SpeedGaming episode ID (if imported from SpeedGaming)"
    )
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
    player_ids: list[int] = Field(
        default_factory=list, description="List of user IDs to add as players"
    )


class MatchUpdateRequest(BaseModel):
    """Request schema for updating a match."""

    stream_channel_id: Optional[int] = Field(None, description="Stream channel ID")
    scheduled_at: Optional[datetime] = Field(None, description="Match scheduled time")
    checked_in_at: Optional[datetime] = Field(None, description="Check-in time")
    started_at: Optional[datetime] = Field(None, description="Match start time")
    finished_at: Optional[datetime] = Field(None, description="Match finish time")
    confirmed_at: Optional[datetime] = Field(
        None, description="Match confirmation time"
    )
    title: Optional[str] = Field(None, max_length=255, description="Match title")
    comment: Optional[str] = Field(None, description="Match comment")


class MatchAdvanceStatusRequest(BaseModel):
    """Request schema for advancing match status."""

    status: str = Field(
        ...,
        description="Target status: 'checked_in', 'started', 'finished', or 'recorded'",
    )


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

    items: list[TournamentPlayerOut] = Field(
        ..., description="List of player registration objects"
    )
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


# ============================================================================
# Tournament Match Settings Schemas
# ============================================================================


class TournamentMatchSettingsOut(BaseModel):
    """Tournament match settings output schema."""

    id: int = Field(..., description="Settings submission ID")
    match_id: int = Field(..., description="Match ID")
    game_number: int = Field(..., description="Game number in match series")
    settings: dict = Field(..., description="Settings data (JSON)")
    submitted: bool = Field(..., description="Whether settings are submitted")
    submitted_by_id: int = Field(..., description="User ID of submitter")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    notes: Optional[str] = Field(None, description="Optional notes from submitter")
    is_valid: bool = Field(..., description="Whether settings passed validation")
    validation_error: Optional[str] = Field(
        None, description="Validation error message if invalid"
    )
    applied: bool = Field(
        ..., description="Whether settings have been applied to generate race"
    )
    applied_at: Optional[datetime] = Field(
        None, description="When settings were applied"
    )

    class Config:
        from_attributes = True


class TournamentMatchSettingsListResponse(BaseModel):
    """Response schema for lists of tournament match settings."""

    items: list[TournamentMatchSettingsOut] = Field(
        ..., description="List of settings submissions"
    )
    count: int = Field(..., description="Total number of submissions in the result")


class TournamentMatchSettingsSubmitRequest(BaseModel):
    """Request schema for submitting tournament match settings."""

    settings: dict = Field(
        ..., description="Settings data (structure varies by tournament type)"
    )
    game_number: int = Field(
        1, ge=1, le=10, description="Game number in match series (1-10)"
    )
    notes: Optional[str] = Field(
        None, max_length=1000, description="Optional notes from submitter"
    )


class TournamentMatchSettingsValidateRequest(BaseModel):
    """Request schema for validating tournament match settings."""

    settings: dict = Field(..., description="Settings data to validate")
    tournament_id: int = Field(
        ..., description="Tournament ID for tournament-specific validation"
    )


class TournamentMatchSettingsValidateResponse(BaseModel):
    """Response schema for settings validation."""

    is_valid: bool = Field(..., description="Whether settings are valid")
    error_message: Optional[str] = Field(None, description="Error message if invalid")
