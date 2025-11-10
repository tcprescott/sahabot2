"""Organization invite schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrganizationInviteOut(BaseModel):
    """Organization invite output schema."""

    id: int = Field(..., description="Invite ID")
    organization_id: int = Field(..., description="Organization ID")
    slug: str = Field(..., description="Invite slug/code")
    created_by_id: int = Field(..., description="User ID of invite creator")
    is_active: bool = Field(..., description="Whether the invite is active")
    max_uses: Optional[int] = Field(
        None, description="Maximum number of uses (null = unlimited)"
    )
    uses_count: int = Field(..., description="Current number of uses")
    expires_at: Optional[datetime] = Field(
        None, description="Invite expiration timestamp (null = never expires)"
    )
    created_at: datetime = Field(..., description="Invite creation timestamp")
    updated_at: datetime = Field(..., description="Invite last update timestamp")

    class Config:
        from_attributes = True


class OrganizationInviteListResponse(BaseModel):
    """Response schema for lists of organization invites."""

    items: list[OrganizationInviteOut] = Field(
        ..., description="List of invite objects"
    )
    count: int = Field(..., description="Total number of invites in the result")


class OrganizationInviteCreateRequest(BaseModel):
    """Request schema for creating an organization invite."""

    slug: str = Field(..., min_length=1, max_length=100, description="Invite slug/code")
    max_uses: Optional[int] = Field(
        None, description="Maximum number of uses (null = unlimited)"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Invite expiration timestamp (null = never expires)"
    )


class OrganizationInviteUpdateRequest(BaseModel):
    """Request schema for updating an organization invite."""

    is_active: Optional[bool] = Field(None, description="Whether the invite is active")
    max_uses: Optional[int] = Field(
        None, description="Maximum number of uses (null = unlimited)"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Invite expiration timestamp (null = never expires)"
    )


class OrganizationInviteUseResponse(BaseModel):
    """Response schema for using an invite."""

    success: bool = Field(..., description="Whether the invite was used successfully")
    message: Optional[str] = Field(None, description="Error or success message")
    organization_id: Optional[int] = Field(
        None, description="Organization ID joined (if successful)"
    )
