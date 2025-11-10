"""API routes for Discord guild (server) management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from api.deps import get_current_user
from models import User
from application.services.discord.discord_guild_service import DiscordGuildService
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discord-guilds", tags=["discord-guilds"])


class DiscordGuildResponse(BaseModel):
    """Response model for Discord guild."""

    id: int
    guild_id: int
    guild_name: str
    guild_icon_url: Optional[str]
    verified_admin: bool
    is_active: bool
    linked_by_username: str

    class Config:
        from_attributes = True


class GuildListResponse(BaseModel):
    """Response for guild list."""

    items: List[DiscordGuildResponse]
    count: int


@router.get(
    "/{organization_id}/invite-url",
    summary="Get Bot Invite URL",
)
async def get_bot_invite_url(
    organization_id: int,
    _: User = Depends(get_current_user),  # Authentication required, user not used
) -> dict:
    """
    Get Discord bot invite URL for adding bot to a server.

    Returns the OAuth2 URL that redirects users to Discord to select
    a server and add the bot. After adding, Discord redirects back
    to the callback URL where we verify permissions.

    Requires authentication (user must be logged in).
    """
    service = DiscordGuildService()

    # Generate callback URL (now a NiceGUI page, not API endpoint)
    base_url = settings.BASE_URL or "http://localhost:8080"
    redirect_uri = f"{base_url}/discord-guild/callback"

    invite_url = service.generate_bot_invite_url(organization_id, redirect_uri)

    return {
        "invite_url": invite_url,
        "organization_id": organization_id,
    }


@router.get(
    "/{organization_id}",
    summary="List Discord Guilds",
)
async def list_guilds(
    organization_id: int, current_user: User = Depends(get_current_user)
) -> GuildListResponse:
    """
    List all Discord guilds linked to an organization.

    Requires organization membership.
    """
    service = DiscordGuildService()
    guilds = await service.list_guilds(current_user, organization_id)

    # Convert to response models
    guild_responses = []
    for guild in guilds:
        await guild.fetch_related("linked_by")
        guild_responses.append(
            DiscordGuildResponse(
                id=guild.id,
                guild_id=guild.guild_id,
                guild_name=guild.guild_name,
                guild_icon_url=guild.guild_icon_url,
                verified_admin=guild.verified_admin,
                is_active=guild.is_active,
                linked_by_username=guild.linked_by.discord_username,
            )
        )

    return GuildListResponse(items=guild_responses, count=len(guild_responses))


@router.delete(
    "/{organization_id}/{guild_id}",
    summary="Unlink Discord Guild",
)
async def unlink_guild(
    organization_id: int, guild_id: int, current_user: User = Depends(get_current_user)
) -> dict:
    """
    Unlink a Discord guild from an organization.

    Requires organization admin/owner permissions.
    """
    service = DiscordGuildService()
    success = await service.unlink_guild(current_user, organization_id, guild_id)

    if not success:
        raise HTTPException(
            status_code=403,
            detail="Failed to unlink guild. Check permissions and guild ownership.",
        )

    return {"success": True, "message": "Discord server unlinked successfully"}
