"""
RaceTime.gg OAuth2 API routes.

This module provides API endpoints for RaceTime.gg account linking via OAuth2.
"""

import logging
import secrets
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from nicegui import app

from api.deps import get_current_user, enforce_rate_limit
from application.services.user_service import UserService
from middleware.racetime_oauth import RacetimeOAuthService
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


@router.get(
    "/link/initiate",
    dependencies=[Depends(enforce_rate_limit)],
    summary="Initiate RaceTime Account Link",
)
async def initiate_link(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> RedirectResponse:
    """
    Initiate RaceTime.gg OAuth2 flow for account linking.

    Redirects the user to RaceTime.gg for authorization.
    """
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)

    # Store state in session for verification in callback
    # Note: In a NiceGUI context, we'd use app.storage.user, but for API routes
    # we need to use the request session or a temporary cache
    # For now, we'll pass it through and verify in callback
    if hasattr(app, 'storage') and hasattr(app.storage, 'user'):
        app.storage.user['racetime_oauth_state'] = state
        app.storage.user['racetime_linking_user_id'] = current_user.id

    # Get authorization URL
    oauth_service = RacetimeOAuthService()
    auth_url = oauth_service.get_authorization_url(state)

    logger.info("User %s initiating RaceTime.gg account link", current_user.id)

    return RedirectResponse(url=auth_url)


@router.get(
    "/link/callback",
    dependencies=[Depends(enforce_rate_limit)],
    summary="RaceTime OAuth Callback",
)
async def link_callback(
    code: str,
    state: str,
    current_user: User | None = Depends(get_current_user)
) -> RedirectResponse:
    """
    Handle OAuth2 callback from RaceTime.gg.

    Completes the account linking process and redirects back to profile.
    """
    try:
        # For API callback, we need to handle authentication differently
        # since this is coming from an external redirect
        # We'll need to check if we have user info in session

        # Verify state (CSRF protection)
        stored_state = None
        user_id = None

        if hasattr(app, 'storage') and hasattr(app.storage, 'user'):
            stored_state = app.storage.user.get('racetime_oauth_state')
            user_id = app.storage.user.get('racetime_linking_user_id')

        # If no current_user from API auth, try to get from session
        if not current_user and user_id:
            user_service = UserService()
            current_user = await user_service.get_user_by_id(user_id)

        if not current_user:
            logger.warning("No user found for RaceTime callback")
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Verify state matches
        if stored_state and state != stored_state:
            logger.warning("State mismatch in RaceTime callback for user %s", current_user.id)
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Exchange code for token
        oauth_service = RacetimeOAuthService()
        token_data = await oauth_service.exchange_code_for_token(code)
        access_token = token_data['access_token']

        # Get user info from RaceTime
        userinfo = await oauth_service.get_user_info(access_token)
        racetime_id = userinfo['id']
        racetime_name = userinfo['name']

        # Link the account
        user_service = UserService()
        await user_service.link_racetime_account(
            user=current_user,
            racetime_id=racetime_id,
            racetime_name=racetime_name,
            access_token=access_token
        )

        logger.info("Successfully linked RaceTime account %s to user %s", racetime_id, current_user.id)

        # Clear state from session
        if hasattr(app, 'storage') and hasattr(app.storage, 'user'):
            app.storage.user.pop('racetime_oauth_state', None)
            app.storage.user.pop('racetime_linking_user_id', None)

        # Redirect back to profile page
        return RedirectResponse(url="/profile")

    except ValueError as e:
        logger.error("Error linking RaceTime account: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error in RaceTime callback: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to link RaceTime account")


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
