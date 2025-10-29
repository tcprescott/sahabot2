"""User schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional


class UserOut(BaseModel):
    """User profile output schema."""
    
    id: int = Field(..., description="Internal user ID")
    discord_id: int = Field(..., description="Discord user ID")
    discord_username: str = Field(..., description="Discord username")
    discord_discriminator: Optional[str] = Field(
        None,
        description="Discord discriminator (deprecated by Discord but kept for compatibility)"
    )
    discord_avatar: Optional[str] = Field(None, description="Discord avatar hash")
    discord_email: Optional[str] = Field(None, description="Discord email address")
    permission: int = Field(
        ...,
        description="User permission level (0=USER, 50=MODERATOR, 100=ADMIN, 200=SUPERADMIN)"
    )
    is_active: bool = Field(..., description="Whether the user account is active")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response schema for lists of users."""
    
    items: list[UserOut] = Field(..., description="List of user objects")
    count: int = Field(..., description="Total number of users in the result")
