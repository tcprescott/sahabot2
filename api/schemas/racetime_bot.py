"""RaceTime bot schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RacetimeBotOut(BaseModel):
    """RaceTime bot output schema."""

    id: int = Field(..., description="Internal bot ID")
    category: str = Field(..., description="RaceTime category slug (e.g., 'alttpr')")
    name: str = Field(..., description="Friendly name for the bot")
    description: Optional[str] = Field(None, description="Optional description")
    client_id: str = Field(..., description="OAuth2 client ID")
    is_active: bool = Field(..., description="Whether the bot is active")
    status: int = Field(..., description="Bot connection status (0=UNKNOWN, 1=CONNECTED, 2=AUTH_FAILED, 3=CONNECTION_ERROR, 4=DISCONNECTED)")
    status_message: Optional[str] = Field(None, description="Status message or error details")
    last_connected_at: Optional[datetime] = Field(None, description="Last successful connection timestamp")
    last_status_check_at: Optional[datetime] = Field(None, description="Last status check timestamp")

    class Config:
        from_attributes = True


class RacetimeBotListResponse(BaseModel):
    """Response schema for lists of RaceTime bots."""

    items: list[RacetimeBotOut] = Field(..., description="List of RaceTime bot objects")
    count: int = Field(..., description="Total number of bots in the result")


class RacetimeBotCreate(BaseModel):
    """Schema for creating a new RaceTime bot."""

    category: str = Field(..., description="RaceTime category slug", min_length=1, max_length=50)
    name: str = Field(..., description="Friendly name for the bot", min_length=1, max_length=255)
    client_id: str = Field(..., description="OAuth2 client ID", min_length=1)
    client_secret: str = Field(..., description="OAuth2 client secret", min_length=1)
    description: Optional[str] = Field(None, description="Optional description")
    is_active: bool = Field(True, description="Whether the bot should be active")


class RacetimeBotUpdate(BaseModel):
    """Schema for updating an existing RaceTime bot."""

    category: Optional[str] = Field(None, description="RaceTime category slug", min_length=1, max_length=50)
    name: Optional[str] = Field(None, description="Friendly name for the bot", min_length=1, max_length=255)
    client_id: Optional[str] = Field(None, description="OAuth2 client ID", min_length=1)
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret", min_length=1)
    description: Optional[str] = Field(None, description="Optional description")
    is_active: Optional[bool] = Field(None, description="Whether the bot is active")
