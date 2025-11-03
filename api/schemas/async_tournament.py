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
