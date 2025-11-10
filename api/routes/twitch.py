"""
Twitch API routes.

This module provides API endpoints for Twitch account status.
OAuth flow is handled via NiceGUI pages (pages/twitch_oauth.py).
"""

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import get_current_user, enforce_rate_limit
from application.services.core.user_service import UserService
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twitch", tags=["twitch"])


class TwitchLinkResponse(BaseModel):
    """Response for Twitch account link status."""

    linked: bool
    twitch_id: str | None = None
    twitch_name: str | None = None
    twitch_display_name: str | None = None


@router.get(
    "/link/status",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Twitch Link Status",
    response_model=TwitchLinkResponse,
)
async def get_link_status(
    current_user: User = Depends(get_current_user),
) -> TwitchLinkResponse:
    """
    Get the current user's Twitch account link status.

    Returns whether the user has a linked Twitch account and basic info.
    """
    return TwitchLinkResponse(
        linked=bool(current_user.twitch_id),
        twitch_id=current_user.twitch_id,
        twitch_name=current_user.twitch_name,
        twitch_display_name=current_user.twitch_display_name,
    )


@router.post(
    "/link/unlink",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Unlink Twitch Account",
)
async def unlink_account(current_user: User = Depends(get_current_user)) -> dict:
    """
    Unlink Twitch account from the current user.

    Removes the Twitch account association.
    """
    user_service = UserService()
    await user_service.unlink_twitch_account(current_user)

    logger.info("User %s unlinked Twitch account", current_user.id)

    return {"success": True, "message": "Twitch account unlinked successfully"}


# Admin endpoints


class TwitchAccountInfo(BaseModel):
    """Twitch account information for admin view."""

    user_id: int
    discord_username: str
    discord_id: int
    twitch_id: str
    twitch_name: str
    twitch_display_name: str
    created_at: str
    twitch_linked_since: str | None = None


class TwitchAccountsResponse(BaseModel):
    """Response for admin Twitch accounts list."""

    accounts: list[TwitchAccountInfo]
    total: int
    limit: int | None
    offset: int


class TwitchStatsResponse(BaseModel):
    """Response for Twitch link statistics."""

    total_users: int
    linked_users: int
    unlinked_users: int
    link_percentage: float


@router.get(
    "/admin/accounts",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get All Twitch Linked Accounts (Admin)",
    response_model=TwitchAccountsResponse,
)
async def get_admin_accounts(
    limit: int | None = None,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
) -> TwitchAccountsResponse:
    """
    Get all users with linked Twitch accounts (admin only).

    Requires admin permissions. Returns empty list if unauthorized.
    """
    user_service = UserService()
    users = await user_service.get_all_twitch_accounts(
        admin_user=current_user, limit=limit, offset=offset
    )

    # Get total count
    total = await user_service.user_repository.count_twitch_linked_users(
        include_inactive=False
    )

    # Convert to response model
    accounts = [
        TwitchAccountInfo(
            user_id=user.id,
            discord_username=user.discord_username,
            discord_id=user.discord_id,
            twitch_id=user.twitch_id,
            twitch_name=user.twitch_name,
            twitch_display_name=user.twitch_display_name,
            created_at=user.created_at.isoformat(),
            twitch_linked_since=(
                user.updated_at.isoformat() if user.updated_at else None
            ),
        )
        for user in users
    ]

    return TwitchAccountsResponse(
        accounts=accounts, total=total, limit=limit, offset=offset
    )


@router.get(
    "/admin/stats",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get Twitch Link Statistics (Admin)",
    response_model=TwitchStatsResponse,
)
async def get_admin_stats(
    current_user: User = Depends(get_current_user),
) -> TwitchStatsResponse:
    """
    Get statistics about Twitch account linking (admin only).

    Requires admin permissions. Returns empty stats if unauthorized.
    """
    user_service = UserService()
    stats = await user_service.get_twitch_link_statistics(admin_user=current_user)

    if not stats:
        # Unauthorized
        return TwitchStatsResponse(
            total_users=0, linked_users=0, unlinked_users=0, link_percentage=0.0
        )

    return TwitchStatsResponse(**stats)


@router.post(
    "/admin/unlink/{user_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Administratively Unlink Twitch Account (Admin)",
)
async def admin_unlink_account(
    user_id: int, current_user: User = Depends(get_current_user)
) -> dict:
    """
    Administratively unlink Twitch account from a user (admin only).

    Requires admin permissions.
    """
    user_service = UserService()
    user = await user_service.admin_unlink_twitch_account(
        user_id=user_id, admin_user=current_user
    )

    if not user:
        return {"success": False, "message": "Unauthorized or user not found"}

    logger.info(
        "Admin %s unlinked Twitch account for user %s", current_user.id, user_id
    )

    return {
        "success": True,
        "message": f"Twitch account unlinked from user {user.discord_username}",
    }
