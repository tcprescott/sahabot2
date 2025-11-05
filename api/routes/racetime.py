"""
RaceTime.gg API routes.

This module provides API endpoints for RaceTime.gg account status.
OAuth flow is handled via NiceGUI pages (pages/racetime_oauth.py).
"""

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import get_current_user, enforce_rate_limit
from application.services.user_service import UserService
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/racetime", tags=["racetime"])


class RacetimeLinkResponse(BaseModel):
    """Response for RaceTime account link status."""
    linked: bool
    racetime_id: str | None = None
    racetime_name: str | None = None


@router.get(
    "/link/status",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get RaceTime Link Status",
    response_model=RacetimeLinkResponse,
)
async def get_link_status(
    current_user: User = Depends(get_current_user)
) -> RacetimeLinkResponse:
    """
    Get the current user's RaceTime.gg account link status.

    Returns whether the user has a linked RaceTime account and basic info.
    """
    return RacetimeLinkResponse(
        linked=bool(current_user.racetime_id),
        racetime_id=current_user.racetime_id,
        racetime_name=current_user.racetime_name,
    )


@router.post(
    "/link/unlink",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Unlink RaceTime Account",
)
async def unlink_account(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Unlink RaceTime.gg account from the current user.

    Removes the RaceTime account association.
    """
    user_service = UserService()
    await user_service.unlink_racetime_account(current_user)

    logger.info("User %s unlinked RaceTime account", current_user.id)

    return {"success": True, "message": "RaceTime account unlinked successfully"}


# Admin endpoints

class RacetimeAccountInfo(BaseModel):
    """RaceTime account information for admin view."""
    user_id: int
    discord_username: str
    discord_id: int
    racetime_id: str
    racetime_name: str
    created_at: str
    racetime_linked_since: str | None = None


class RacetimeAccountsResponse(BaseModel):
    """Response for admin RaceTime accounts list."""
    accounts: list[RacetimeAccountInfo]
    total: int
    limit: int | None
    offset: int


class RacetimeStatsResponse(BaseModel):
    """Response for RaceTime link statistics."""
    total_users: int
    linked_users: int
    unlinked_users: int
    link_percentage: float


@router.get(
    "/admin/accounts",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get All RaceTime Linked Accounts (Admin)",
    response_model=RacetimeAccountsResponse,
)
async def get_admin_accounts(
    limit: int | None = None,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
) -> RacetimeAccountsResponse:
    """
    Get all users with linked RaceTime accounts (admin only).

    Requires admin permissions. Returns empty list if unauthorized.
    """
    user_service = UserService()
    users = await user_service.get_all_racetime_accounts(
        admin_user=current_user,
        limit=limit,
        offset=offset
    )

    # Get total count
    total = await user_service.user_repository.count_racetime_linked_users(
        include_inactive=False
    )

    # Convert to response model
    accounts = [
        RacetimeAccountInfo(
            user_id=user.id,
            discord_username=user.discord_username,
            discord_id=user.discord_id,
            racetime_id=user.racetime_id,
            racetime_name=user.racetime_name,
            created_at=user.created_at.isoformat(),
            racetime_linked_since=user.updated_at.isoformat() if user.updated_at else None
        )
        for user in users
    ]

    return RacetimeAccountsResponse(
        accounts=accounts,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/admin/stats",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Get RaceTime Link Statistics (Admin)",
    response_model=RacetimeStatsResponse,
)
async def get_admin_stats(
    current_user: User = Depends(get_current_user)
) -> RacetimeStatsResponse:
    """
    Get statistics about RaceTime account linking (admin only).

    Requires admin permissions. Returns empty stats if unauthorized.
    """
    user_service = UserService()
    stats = await user_service.get_racetime_link_statistics(admin_user=current_user)

    if not stats:
        # Unauthorized
        return RacetimeStatsResponse(
            total_users=0,
            linked_users=0,
            unlinked_users=0,
            link_percentage=0.0
        )

    return RacetimeStatsResponse(**stats)


@router.post(
    "/admin/unlink/{user_id}",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Administratively Unlink RaceTime Account (Admin)",
)
async def admin_unlink_account(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Administratively unlink RaceTime account from a user (admin only).

    Requires admin permissions.
    """
    user_service = UserService()
    user = await user_service.admin_unlink_racetime_account(
        user_id=user_id,
        admin_user=current_user
    )

    if not user:
        return {"success": False, "message": "Unauthorized or user not found"}

    logger.info("Admin %s unlinked RaceTime account for user %s", current_user.id, user_id)

    return {
        "success": True,
        "message": f"RaceTime account unlinked from user {user.discord_username}"
    }

