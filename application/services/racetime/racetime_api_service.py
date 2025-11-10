"""
RaceTime.gg API service for making authenticated API calls.

This service handles API calls to RaceTime.gg using stored user access tokens,
with automatic token refresh when tokens are expired.
"""

import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from models import User
from config import settings

logger = logging.getLogger(__name__)


class RacetimeApiService:
    """
    Service for making authenticated RaceTime.gg API calls.

    This service automatically refreshes access tokens when needed and
    provides methods for common RaceTime.gg API operations.
    """

    def __init__(self):
        """Initialize the RaceTime API service."""
        self.racetime_url = settings.RACETIME_URL
        self.token_refresh_buffer = timedelta(
            minutes=5
        )  # Refresh if expiring within 5 minutes

    async def _ensure_valid_token(self, user: User) -> str:
        """
        Ensure user has a valid access token, refreshing if necessary.

        Args:
            user: User with linked RaceTime account

        Returns:
            str: Valid access token

        Raises:
            ValueError: If user has no linked account
            httpx.HTTPError: If token refresh fails
        """
        from application.services.core.user_service import UserService

        if not user.racetime_id or not user.racetime_access_token:
            raise ValueError("User has no linked RaceTime account")

        # Check if token is expired or expiring soon
        if user.racetime_token_expires_at:
            now = datetime.now(timezone.utc)
            if user.racetime_token_expires_at <= now + self.token_refresh_buffer:
                logger.info(
                    "RaceTime token for user %s is expired or expiring soon, refreshing",
                    user.id,
                )

                # Check if we have a refresh token
                if not user.racetime_refresh_token:
                    logger.warning(
                        "User %s has expired token but no refresh token", user.id
                    )
                    raise ValueError(
                        "RaceTime token is expired and no refresh token available"
                    )

                # Refresh the token
                user_service = UserService()
                user = await user_service.refresh_racetime_token(user)
                logger.info(
                    "Successfully refreshed RaceTime token for user %s", user.id
                )

        return user.racetime_access_token

    async def _make_api_request(
        self, user: User, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request to RaceTime.gg.

        Args:
            user: User making the request
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            Dict[str, Any]: JSON response from API

        Raises:
            ValueError: If user has no linked account
            httpx.HTTPError: If API request fails
        """
        # Ensure we have a valid token
        access_token = await self._ensure_valid_token(user)

        # Make the API request
        url = f"{self.racetime_url}{endpoint}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {access_token}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method, url=url, headers=headers, **kwargs
            )

            if response.status_code != 200:
                logger.error(
                    "RaceTime API request failed: %s %s - status %s",
                    method,
                    endpoint,
                    response.status_code,
                )
                raise httpx.HTTPStatusError(
                    f"RaceTime API request failed",
                    request=response.request,
                    response=response,
                )

            return response.json()

    async def get_user_data(self, user: User) -> Dict[str, Any]:
        """
        Get RaceTime user data for the authenticated user.

        Args:
            user: User with linked RaceTime account

        Returns:
            Dict[str, Any]: RaceTime user data

        Raises:
            ValueError: If user has no linked account
            httpx.HTTPError: If API request fails
        """
        return await self._make_api_request(user, "GET", "/o/userinfo")

    async def get_user_races(
        self, user: User, category: Optional[str] = None, show_entrants: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get race history for a RaceTime user.

        Args:
            user: User with linked RaceTime account
            category: Optional category filter (e.g., 'alttpr')
            show_entrants: Include entrant details in response

        Returns:
            List[Dict[str, Any]]: List of race data

        Raises:
            ValueError: If user has no linked account
            httpx.HTTPError: If API request fails
        """
        if not user.racetime_id:
            raise ValueError("User has no linked RaceTime account")

        # Build endpoint
        endpoint = f"/user/{user.racetime_id}/races/data"
        params = {}
        if show_entrants:
            params["show_entrants"] = "true"

        response = await self._make_api_request(user, "GET", endpoint, params=params)

        # Filter by category if specified
        races = response.get("races", [])
        if category:
            races = [r for r in races if r.get("category", {}).get("slug") == category]

        return races

    async def get_user_stats(self, user: User, category: str) -> Dict[str, Any]:
        """
        Get statistics for a user in a specific category.

        Args:
            user: User with linked RaceTime account
            category: Category slug (e.g., 'alttpr')

        Returns:
            Dict[str, Any]: User statistics for the category

        Raises:
            ValueError: If user has no linked account
            httpx.HTTPError: If API request fails
        """
        if not user.racetime_id:
            raise ValueError("User has no linked RaceTime account")

        endpoint = f"/{category}/user/{user.racetime_id}/data"
        return await self._make_api_request(user, "GET", endpoint)

    async def get_race_data(self, user: User, race_name: str) -> Dict[str, Any]:
        """
        Get data for a specific race.

        Args:
            user: User with linked RaceTime account
            race_name: Race identifier (e.g., 'alttpr/famous-shulk-1234')

        Returns:
            Dict[str, Any]: Race data

        Raises:
            ValueError: If user has no linked account
            httpx.HTTPError: If API request fails
        """
        endpoint = f"/{race_name}/data"
        return await self._make_api_request(user, "GET", endpoint)

    async def get_past_races(
        self, user: User, category: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get past races for a category with pagination.

        Args:
            user: User with linked RaceTime account
            category: Category slug (e.g., 'alttpr')
            limit: Maximum number of races to return

        Returns:
            List[Dict[str, Any]]: List of race data

        Raises:
            ValueError: If user has no linked account
            httpx.HTTPError: If API request fails
        """
        endpoint = f"/{category}/races/data"
        params = {"show_entrants": "true"}

        response = await self._make_api_request(user, "GET", endpoint, params=params)

        races = response.get("races", [])

        # Filter to races the user participated in and limit
        if user.racetime_id:
            user_races = []
            for race in races:
                entrants = race.get("entrants", [])
                if any(
                    e.get("user", {}).get("id") == user.racetime_id for e in entrants
                ):
                    user_races.append(race)
                    if len(user_races) >= limit:
                        break
            return user_races

        return races[:limit]
