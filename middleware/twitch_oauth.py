"""
Twitch OAuth2 service for account linking.

This module handles OAuth2 authentication flow with Twitch for linking user accounts.
"""

import httpx
import logging
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from config import settings

logger = logging.getLogger(__name__)


class TwitchOAuthService:
    """
    Service for handling Twitch OAuth2 authentication and account linking.

    This service manages the OAuth2 flow with Twitch to link user accounts.
    """

    def __init__(self):
        """Initialize the Twitch OAuth service."""
        self.twitch_auth_url = "https://id.twitch.tv/oauth2"
        self.twitch_api_url = "https://api.twitch.tv/helix"
        self.client_id = settings.TWITCH_CLIENT_ID
        self.client_secret = settings.TWITCH_CLIENT_SECRET
        self.redirect_uri = settings.get_twitch_oauth_redirect_uri()

    def get_authorization_url(self, state: str) -> str:
        """
        Generate Twitch OAuth2 authorization URL.

        Args:
            state: CSRF protection state parameter

        Returns:
            str: Authorization URL
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'state': state,
            'force_verify': 'true'
        }

        query_string = urlencode(params)
        return f"{self.twitch_auth_url}/authorize?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Twitch

        Returns:
            Dict[str, Any]: Token response from Twitch

        Raises:
            httpx.HTTPError: If token exchange fails
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.twitch_auth_url}/token",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            # Log error details if request fails
            if response.status_code != 200:
                # Don't log the full error response
                logger.error(
                    "Twitch token exchange failed with status %s",
                    response.status_code
                )
                raise httpx.HTTPStatusError(
                    "Twitch token exchange failed",
                    request=response.request,
                    response=response
                )

            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Twitch refresh token

        Returns:
            Dict[str, Any]: Token response with new access token

        Raises:
            httpx.HTTPError: If token refresh fails
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.twitch_auth_url}/token",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code != 200:
                logger.error(
                    "Twitch token refresh failed with status %s",
                    response.status_code
                )
                raise httpx.HTTPStatusError(
                    "Twitch token refresh failed",
                    request=response.request,
                    response=response
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
        Get user information from Twitch.

        Args:
            access_token: Twitch access token

        Returns:
            Dict[str, Any]: User information from Twitch

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.twitch_api_url}/users",
                headers={
                    'Authorization': f"Bearer {access_token}",
                    'Client-Id': self.client_id
                }
            )

            if response.status_code != 200:
                # Don't log the full error response
                logger.error(
                    "Twitch userinfo request failed with status %s",
                    response.status_code
                )
                raise httpx.HTTPStatusError(
                    "Twitch userinfo request failed",
                    request=response.request,
                    response=response
                )

            data = response.json()
            # Twitch returns data in a 'data' array with user info
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]
            else:
                logger.error("Twitch userinfo response missing data")
                raise ValueError("Invalid Twitch userinfo response")
