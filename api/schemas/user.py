"""User schemas for API responses."""

from pydantic import BaseModel
from typing import Optional


class UserOut(BaseModel):
    id: int
    discord_id: int
    discord_username: str
    discord_discriminator: Optional[str] = None
    discord_avatar: Optional[str] = None
    discord_email: Optional[str] = None
    permission: int
    is_active: bool

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserOut]
    count: int
