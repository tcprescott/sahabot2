"""
RaceTime.gg OAuth2 service for account linking.

This module handles OAuth2 authentication flow with RaceTime.gg for linking user accounts.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from config import settings

logger = logging.getLogger(__name__)


class RacetimeOAuthService:
    """
    Service for handling RaceTime.gg OAuth2 authentication and account linking.

    This service manages the OAuth2 flow with RaceTime.gg to link user accounts.
    """

    def __init__(self):
        """Initialize the RaceTime OAuth service."""
        self.racetime_url = settings.RACETIME_URL
        self.client_id = settings.RACETIME_CLIENT_ID
        self.client_secret = settings.RACETIME_CLIENT_SECRET
        self.redirect_uri = settings.get_racetime_oauth_redirect_uri()

    def get_authorization_url(self, state: str) -> str:
        """
        Generate RaceTime.gg OAuth2 authorization URL.

        Args:
            state: CSRF protection state parameter

        Returns:
            str: Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "read",
            "state": state,
        }

        query_string = urlencode(params)
        return f"{self.racetime_url}/o/authorize?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from RaceTime.gg

        Returns:
            Dict[str, Any]: Token response from RaceTime.gg

        Raises:
            httpx.HTTPError: If token exchange fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "scope": "read",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.racetime_url}/o/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            # Log error details if request fails
            if response.status_code != 200:
                # Don't log the full error response as it may contain sensitive info
                logger.error(
                    "RaceTime.gg token exchange failed with status %s",
                    response.status_code,
                )
                raise httpx.HTTPStatusError(
                    "RaceTime.gg token exchange failed",
                    request=response.request,
                    response=response,
                )

            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: RaceTime.gg refresh token

        Returns:
            Dict[str, Any]: Token response with new access token

        Raises:
            httpx.HTTPError: If token refresh fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.racetime_url}/o/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                logger.error(
                    "RaceTime.gg token refresh failed with status %s",
                    response.status_code,
                )
                raise httpx.HTTPStatusError(
                    "RaceTime.gg token refresh failed",
                    request=response.request,
                    response=response,
                )

            return response.json()

    def calculate_token_expiry(self, expires_in: int) -> datetime:
        """
        Calculate token expiration datetime.

        Args:
            expires_in: Seconds until token expires

        Returns:
            datetime: Token expiration timestamp (timezone-aware UTC)
        """
        return datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from RaceTime.gg.

        Args:
            access_token: RaceTime.gg access token

        Returns:
            Dict[str, Any]: User information from RaceTime.gg

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.racetime_url}/o/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                # Don't log the full error response as it may contain sensitive info
                logger.error(
                    "RaceTime.gg userinfo request failed with status %s",
                    response.status_code,
                )
                raise httpx.HTTPStatusError(
                    "RaceTime.gg userinfo request failed",
                    request=response.request,
                    response=response,
                )

            return response.json()
