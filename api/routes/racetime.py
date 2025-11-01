"""
RaceTime.gg OAuth2 API routes.

This module provides API endpoints for RaceTime.gg account linking via OAuth2.
"""

import logging
import secrets
from typing import Any
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
    summary="Initiate RaceTime Account Link",
)
async def initiate_link(
    request: Request,
) -> RedirectResponse:
    """
    Initiate RaceTime.gg OAuth2 flow for account linking.

    Redirects the user to RaceTime.gg for authorization.

    Note: This endpoint does not use standard API authentication because it's accessed
    from the web UI. Authentication is verified via session state.
    """
    # Get current user from session
    user_id = _get_session_value('user_id')

    if not user_id:
        logger.warning("Unauthenticated user attempted to initiate RaceTime link")
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)

    # Store state in session for verification in callback
    _set_session_value('racetime_oauth_state', state)
    _set_session_value('racetime_linking_user_id', user_id)

    # Get authorization URL
    oauth_service = RacetimeOAuthService()
    auth_url = oauth_service.get_authorization_url(state)

    logger.info("User %s initiating RaceTime.gg account link", user_id)

    return RedirectResponse(url=auth_url)


@router.get(
    "/link/callback",
    summary="RaceTime OAuth Callback",
)
async def link_callback(
    code: str,
    state: str,
) -> RedirectResponse:
    """
    Handle OAuth2 callback from RaceTime.gg.

    Completes the account linking process and redirects back to profile.

    Note: This endpoint does not use standard API authentication because it's called
    by an external OAuth redirect. Instead, it relies on session state stored during
    the initiation step.
    """
    try:
        # Get user from session state
        stored_state = _get_session_value('racetime_oauth_state')
        user_id = _get_session_value('racetime_linking_user_id')

        if not user_id:
            logger.warning("No user ID found in session for RaceTime callback")
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Verify state matches (CSRF protection)
        # Both stored_state and state must be present and match
        if not stored_state or not state or state != stored_state:
            logger.warning("State mismatch in RaceTime callback for user %s (stored: %s, received: %s)", user_id, bool(stored_state), bool(state))
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Get user from database
        user_service = UserService()
        current_user = await user_service.get_user_by_id(user_id)

        if not current_user:
            logger.warning("User %s not found for RaceTime callback", user_id)
            raise HTTPException(status_code=401, detail="User not found")

        # Exchange code for token
        oauth_service = RacetimeOAuthService()
        token_data = await oauth_service.exchange_code_for_token(code)
        access_token = token_data['access_token']

        # Get user info from RaceTime
        userinfo = await oauth_service.get_user_info(access_token)
        racetime_id = userinfo['id']
        racetime_name = userinfo['name']

        # Link the account
        await user_service.link_racetime_account(
            user=current_user,
            racetime_id=racetime_id,
            racetime_name=racetime_name,
            access_token=access_token
        )

        logger.info("Successfully linked RaceTime account %s to user %s", racetime_id, current_user.id)

        # Clear state from session
        _remove_session_value('racetime_oauth_state')
        _remove_session_value('racetime_linking_user_id')

        # Redirect back to profile page
        return RedirectResponse(url="/profile")

    except ValueError as e:
        logger.error("Error linking RaceTime account: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error in RaceTime callback: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to link RaceTime account")


def _get_session_value(key: str) -> Any | None:
    """
    Helper function to safely get a value from the NiceGUI session storage.

    Args:
        key: Session storage key

    Returns:
        Value from session or None if not available
    """
    if hasattr(app, 'storage') and hasattr(app.storage, 'user'):
        return app.storage.user.get(key)
    return None


def _set_session_value(key: str, value: Any) -> None:
    """
    Helper function to safely set a value in the NiceGUI session storage.

    Args:
        key: Session storage key
        value: Value to store
    """
    if hasattr(app, 'storage') and hasattr(app.storage, 'user'):
        app.storage.user[key] = value


def _remove_session_value(key: str) -> None:
    """
    Helper function to safely remove a value from the NiceGUI session storage.

    Args:
        key: Session storage key
    """
    if hasattr(app, 'storage') and hasattr(app.storage, 'user'):
        app.storage.user.pop(key, None)


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
