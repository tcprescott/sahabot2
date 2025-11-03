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
