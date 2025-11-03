"""Service layer for Discord guild (server) management.

Handles linking Discord servers to organizations with permission verification.
"""

from __future__ import annotations
from typing import Optional, List
import logging
import httpx
from urllib.parse import urlencode

from models import User
from models.discord_guild import DiscordGuild
from application.repositories.discord_guild_repository import DiscordGuildRepository
from application.services.organization_service import OrganizationService
from application.services.authorization_service import AuthorizationService
from config import settings

logger = logging.getLogger(__name__)

# Discord API endpoints
DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_OAUTH_AUTHORIZE = "https://discord.com/oauth2/authorize"


class DiscordGuildService:
    """Service for managing Discord guild connections to organizations."""

    def __init__(self):
        self.repo = DiscordGuildRepository()
        self.org_service = OrganizationService()
        self.auth_service = AuthorizationService()

    def generate_bot_invite_url(self, organization_id: int, redirect_uri: str) -> str:
        """
        Generate Discord bot invite URL with OAuth2 flow.

        This uses the 'bot' scope with 'guilds' scope to get guild info during install.
        The redirect_uri should be the callback URL to verify permissions.

        Args:
            organization_id: Organization ID to associate the guild with
            redirect_uri: Callback URL after bot is added

        Returns:
            Discord OAuth2 authorization URL
        """
        params = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'scope': 'bot guilds',  # bot scope + guilds to read guild info
            'permissions': '0',  # No permissions requested (will be configured later)
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': f'org:{organization_id}',  # Pass org ID in state
        }

        url = f"{DISCORD_OAUTH_AUTHORIZE}?{urlencode(params)}"
        logger.info("Generated bot invite URL for org %s", organization_id)
        return url

    async def verify_and_link_guild(
        self,
        user: User,
        organization_id: int,
        code: str,
        redirect_uri: str,
        guild_id: Optional[str] = None
    ) -> Optional[DiscordGuild]:
        """
        Verify OAuth2 code and link guild to organization.

        This exchanges the OAuth2 code for tokens, verifies the user has
        admin permissions in the guild, and creates the guild link.

        Args:
            user: User linking the guild
            organization_id: Organization to link to
            code: OAuth2 authorization code
            redirect_uri: Redirect URI used in OAuth2 flow
            guild_id: Discord guild ID (from callback, if provided)

        Returns:
            Created DiscordGuild or None if verification failed
        """
        # Verify user has permission to manage this organization
        member = await self.org_service.get_member(organization_id, user.id)
        if not member:
            logger.warning(
                "User %s attempted to link guild to org %s without membership",
                user.id,
                organization_id
            )
            return None

        logger.info(
            "User %s linking guild %s to org %s",
            user.id,
            guild_id or "(unknown)",
            organization_id
        )

        # Exchange code for access token
        token_data = await self._exchange_code(code, redirect_uri)
        if not token_data:
            logger.error("Failed to exchange OAuth2 code for org %s", organization_id)
            return None

        access_token = token_data.get('access_token')
        if not access_token:
            logger.error("No access token in response for org %s", organization_id)
            return None

        logger.debug("Successfully obtained access token")

        # Get user's guilds to verify they have admin permissions
        guild_info = await self._get_user_guild_info(access_token, guild_id)
        if not guild_info:
            logger.error(
                "Failed to get guild info from Discord API (guild_id=%s)",
                guild_id or "not provided"
            )
            return None

        logger.debug("Guild info retrieved: %s", guild_info.get('name'))

        # The guild they added the bot to should be in their guilds list
        # We need to verify they have admin (0x8) permission
        actual_guild_id = guild_info.get('id')
        permissions = int(guild_info.get('permissions', 0))

        # Check for Administrator permission (0x8)
        ADMINISTRATOR = 0x8
        if not (permissions & ADMINISTRATOR):
            logger.warning(
                "User %s does not have admin permissions in guild %s",
                user.id,
                actual_guild_id
            )
            return None

        # Check if guild is already linked
        existing = await self.repo.get_by_guild_id(int(actual_guild_id))
        if existing:
            logger.warning(
                "Guild %s is already linked to org %s",
                actual_guild_id,
                existing.organization_id
            )
            return None

        # Create the guild link
        guild = await self.repo.create(
            organization_id=organization_id,
            guild_id=int(actual_guild_id),
            guild_name=guild_info.get('name', 'Unknown'),
            guild_icon=guild_info.get('icon'),
            linked_by_user_id=user.id,
            verified_admin=True,
        )

        logger.info(
            "Linked guild %s (%s) to org %s by user %s",
            actual_guild_id,
            guild.guild_name,
            organization_id,
            user.id
        )

        return guild

    async def _exchange_code(self, code: str, redirect_uri: str) -> Optional[dict]:
        """Exchange OAuth2 code for access token."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{DISCORD_API_BASE}/oauth2/token",
                    data={
                        'client_id': settings.DISCORD_CLIENT_ID,
                        'client_secret': settings.DISCORD_CLIENT_SECRET,
                        'grant_type': 'authorization_code',
                        'code': code,
                        'redirect_uri': redirect_uri,
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Error exchanging OAuth2 code: %s", e)
                return None

    async def _get_user_guild_info(self, access_token: str, guild_id: Optional[str] = None) -> Optional[dict]:
        """
        Get guild info from Discord API using access token.

        Args:
            access_token: OAuth2 access token
            guild_id: Specific guild ID to look for (if provided)

        Returns:
            Guild info dict or None if not found/error
        """
        async with httpx.AsyncClient() as client:
            try:
                # Get user's guilds
                response = await client.get(
                    f"{DISCORD_API_BASE}/users/@me/guilds",
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                guilds = response.json()

                # If guild_id provided, find that specific guild
                if guild_id:
                    for guild in guilds:
                        if str(guild.get('id')) == str(guild_id):
                            return guild
                    logger.warning("Guild %s not found in user's guild list", guild_id)
                    return None

                # Otherwise return the first guild (fallback for old flow)
                if guilds:
                    return guilds[0]

                return None
            except Exception as e:
                logger.error("Error fetching guild info: %s", e)
                return None

    async def list_guilds(
        self,
        user: Optional[User],
        organization_id: int
    ) -> List[DiscordGuild]:
        """
        List Discord guilds for an organization.

        Args:
            user: User making the request
            organization_id: Organization ID

        Returns:
            List of guilds (empty if unauthorized)
        """
        member = await self.org_service.get_member(organization_id, user.id)
        if not member:
            logger.warning(
                "Unauthorized list_guilds by user %s for org %s",
                getattr(user, 'id', None),
                organization_id
            )
            return []

        return await self.repo.list_by_organization(organization_id)

    async def unlink_guild(
        self,
        user: Optional[User],
        organization_id: int,
        guild_pk: int
    ) -> bool:
        """
        Unlink a Discord guild from an organization.

        Args:
            user: User making the request
            organization_id: Organization ID
            guild_pk: Guild primary key

        Returns:
            True if successful, False otherwise
        """
        # Verify user is org admin/owner
        if not await self.org_service.user_can_admin_org(user, organization_id):
            logger.warning(
                "Unauthorized unlink_guild by user %s for org %s",
                getattr(user, 'id', None),
                organization_id
            )
            return False

        # Verify guild belongs to organization
        guild = await self.repo.get_by_id(guild_pk)
        if not guild or guild.organization_id != organization_id:
            logger.warning(
                "Guild %s does not belong to org %s",
                guild_pk,
                organization_id
            )
            return False

        # Delete the guild link
        success = await self.repo.delete(guild_pk)
        if success:
            logger.info(
                "Unlinked guild %s from org %s by user %s",
                guild.guild_id,
                organization_id,
                user.id if user else None
            )

        return success
