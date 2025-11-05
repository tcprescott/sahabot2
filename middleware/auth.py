"""
Discord OAuth2 authentication middleware.

This module handles Discord OAuth2 authentication flow.
"""

import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from config import settings
from nicegui import app, ui
from application.services.user_service import UserService
from application.services.audit_service import AuditService
from application.repositories.user_repository import UserRepository
from models import User


logger = logging.getLogger(__name__)


class DiscordAuthService:
    """
    Service for handling Discord OAuth2 authentication.
    
    This service manages the OAuth2 flow with Discord and user session management.
    """
    
    DISCORD_API_BASE = "https://discord.com/api/v10"
    DISCORD_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
    DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
    
    def __init__(self):
        """Initialize the Discord auth service."""
        self.user_service = UserService()
        self.audit_service = AuditService()
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate Discord OAuth2 authorization URL.
        
        Args:
            state: CSRF protection state parameter
            
        Returns:
            str: Authorization URL
        """
        params = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'redirect_uri': settings.DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify',
            'state': state
        }
        
        query_string = urlencode(params)
        return f"{self.DISCORD_AUTHORIZE_URL}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Discord
            
        Returns:
            Dict[str, Any]: Token response from Discord
            
        Raises:
            httpx.HTTPError: If token exchange fails
        """
        data = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'client_secret': settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.DISCORD_REDIRECT_URI,
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.DISCORD_TOKEN_URL,
                data=data,
                headers=headers
            )
            
            # Log error details if request fails
            if response.status_code != 200:
                error_text = response.text
                raise httpx.HTTPStatusError(
                    f"Discord token exchange failed: {error_text}",
                    request=response.request,
                    response=response
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Discord.
        
        Args:
            access_token: Discord access token
            
        Returns:
            Dict[str, Any]: User information from Discord
            
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.DISCORD_API_BASE}/users/@me",
                headers={'Authorization': f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def refresh_discord_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Discord access token using refresh token.

        Args:
            refresh_token: Discord refresh token

        Returns:
            Dict[str, Any]: Token response containing access_token, refresh_token, expires_in

        Raises:
            httpx.HTTPError: If token refresh fails
        """
        data = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'client_secret': settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.DISCORD_TOKEN_URL,
                data=data,
                headers=headers
            )

            # Log error details if request fails
            if response.status_code != 200:
                error_text = response.text
                raise httpx.HTTPStatusError(
                    f"Discord token refresh failed: {error_text}",
                    request=response.request,
                    response=response
                )

            return response.json()

    @staticmethod
    def calculate_token_expiry(expires_in: int) -> datetime:
        """
        Calculate token expiration timestamp.

        Args:
            expires_in: Number of seconds until token expires

        Returns:
            datetime: Token expiration timestamp (timezone-aware UTC)
        """
        return datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    @staticmethod
    def is_discord_token_expired(user: 'User', buffer_minutes: int = 5) -> bool:
        """
        Check if Discord access token is expired or expiring soon.

        Args:
            user: User to check token for
            buffer_minutes: Minutes before expiration to consider token expired (default 5)

        Returns:
            bool: True if token is expired or will expire within buffer time
        """
        if not user.discord_token_expires_at:
            return True  # No expiration time means token needs refresh

        # Consider token expired if it expires within buffer time
        buffer_time = datetime.now(timezone.utc) + timedelta(minutes=buffer_minutes)
        return user.discord_token_expires_at <= buffer_time

    async def authenticate_user(self, code: str, ip_address: Optional[str] = None) -> User:
        """
        Authenticate user with Discord OAuth2 code.
        
        Args:
            code: Authorization code from Discord
            ip_address: IP address of the user
            
        Returns:
            User: Authenticated user
            
        Raises:
            Exception: If authentication fails
        """
        try:
            # Exchange code for token
            logger.info("Attempting to exchange authorization code for token")
            token_data = await self.exchange_code_for_token(code)
            access_token = token_data['access_token']
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 604800)  # Default 7 days if not provided
            logger.info("Successfully obtained access token")

            # Calculate token expiration
            expires_at = self.calculate_token_expiry(expires_in)

            # Get user info from Discord
            logger.info("Fetching user info from Discord")
            discord_user = await self.get_user_info(access_token)
            logger.info("Successfully retrieved user info for Discord ID: %s", discord_user['id'])

            # Get or create user in database
            user = await self.user_service.get_or_create_user_from_discord(
                discord_id=int(discord_user['id']),
                discord_username=discord_user['username'],
                discord_discriminator=discord_user.get('discriminator'),
                discord_avatar=discord_user.get('avatar')
            )

            # Store OAuth2 tokens for automatic refresh
            if refresh_token:
                await self.user_service.update_discord_tokens(
                    user=user,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at
                )
                logger.info("Stored Discord OAuth2 tokens for user %s", user.id)

            # Log the login
            await self.audit_service.log_login(user, ip_address)
            
            return user
        except httpx.HTTPStatusError as e:
            logger.error("Discord OAuth2 error: Status %s", e.response.status_code)
            logger.error("Response body: %s", e.response.text)
            raise Exception(f"Discord authentication failed: {e.response.text}")
        except Exception as e:
            logger.error("Authentication error: %s", str(e), exc_info=True)
            raise

        
        return user
    
    @staticmethod
    async def get_current_user() -> Optional[User]:
        """
        Get current authenticated user from session with automatic token refresh.

        This method automatically refreshes the Discord access token if it's expired
        or expiring soon (within 5 minutes). If refresh fails, the user session is
        cleared and None is returned.

        Returns:
            Optional[User]: Current user with valid token or None if not authenticated
        """
        user_id = app.storage.user.get('user_id')
        if not user_id:
            return None

        # Fetch fresh user data from database
        user_repo = UserRepository()
        user = await user_repo.get_by_id(user_id)

        if not user:
            # User was deleted, clear session
            await DiscordAuthService.clear_current_user()
            return None

        # Check if Discord token needs refresh
        if DiscordAuthService.is_discord_token_expired(user):
            logger.info("Discord token expired for user %s, attempting refresh", user.id)
            try:
                # Refresh the token
                user_service = UserService()
                user = await user_service.refresh_discord_token(user)
                logger.info("Successfully refreshed Discord token for user %s", user.id)
            except Exception as e:
                # Token refresh failed (invalid/revoked refresh token)
                logger.warning(
                    "Failed to refresh Discord token for user %s: %s",
                    user.id,
                    str(e)
                )
                # Clear session to force re-login
                await DiscordAuthService.clear_current_user()
                return None

        return user
    
    @staticmethod
    async def set_current_user(user: User) -> None:
        """
        Set current authenticated user in session.
        
        Args:
            user: User to set as current
        """
        # Only store serializable data (not the ORM object)
        app.storage.user['user_id'] = user.id
        app.storage.user['discord_id'] = user.discord_id
        app.storage.user['permission'] = user.permission.value
    
    @staticmethod
    async def clear_current_user() -> None:
        """Clear current user from session (logout)."""
        app.storage.user.clear()
    
    @staticmethod
    async def require_auth(redirect_to: str = '/') -> Optional[User]:
        """
        Require authentication for current page.
        
        Args:
            redirect_to: URL to redirect to after login
            
        Returns:
            Optional[User]: Current user if authenticated
        """
        user = await DiscordAuthService.get_current_user()
        if not user:
            app.storage.user['redirect_after_login'] = redirect_to
            ui.navigate.to('/auth/login')
            return None
        return user
    
    @staticmethod
    async def require_permission(permission: int, redirect_to: str = '/') -> Optional[User]:
        """
        Require specific permission level for current page.
        
        Args:
            permission: Required permission level
            redirect_to: URL to redirect to if unauthorized
            
        Returns:
            Optional[User]: Current user if authorized
        """
        user = await DiscordAuthService.get_current_user()
        
        if not user:
            app.storage.user['redirect_after_login'] = redirect_to
            ui.navigate.to('/auth/login')
            return None
        
        if not user.has_permission(permission):
            ui.navigate.to('/')
            ui.notify('You do not have permission to access this page', type='negative')
            return None
        
        return user
