"""
Discord OAuth2 authentication middleware.

This module handles Discord OAuth2 authentication flow.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from config import settings
from nicegui import app, ui
from application.services.user_service import UserService
from application.services.audit_service import AuditService
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
            'scope': 'identify email',
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
            logger.info("Successfully obtained access token")
            
            # Get user info from Discord
            logger.info("Fetching user info from Discord")
            discord_user = await self.get_user_info(access_token)
            logger.info("Successfully retrieved user info for Discord ID: %s", discord_user['id'])
            
            # Get or create user in database
            user = await self.user_service.get_or_create_user_from_discord(
                discord_id=int(discord_user['id']),
                discord_username=discord_user['username'],
                discord_discriminator=discord_user.get('discriminator'),
                discord_avatar=discord_user.get('avatar'),
                discord_email=discord_user.get('email')
            )
            
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
        Get current authenticated user from session.
        
        Returns:
            Optional[User]: Current user or None if not authenticated
        """
        user_id = app.storage.user.get('user_id')
        if not user_id:
            return None
        
        # Fetch fresh user data from database
        from application.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        return await user_repo.get_by_id(user_id)
    
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
