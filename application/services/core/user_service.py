"""
User service for user-related business logic.

This module contains all business logic related to user management.
"""

import logging
from datetime import datetime
from models import User, Permission, SYSTEM_USER_ID
from typing import Optional
from application.repositories.user_repository import UserRepository
from application.events import EventBus, UserCreatedEvent, UserPermissionChangedEvent

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for handling user-related business logic.

    This service encapsulates all business rules and operations related to users,
    keeping the logic separate from the UI and data access layers.
    """

    def __init__(self):
        """Initialize the user service with required repositories."""
        self.user_repository = UserRepository()

    async def get_or_create_user_from_discord(
        self,
        discord_id: int,
        discord_username: str,
        discord_discriminator: Optional[str] = None,
        discord_avatar: Optional[str] = None,
    ) -> User:
        """
        Get or create a user from Discord OAuth data.

        Args:
            discord_id: Discord user ID
            discord_username: Discord username
            discord_discriminator: Discord discriminator
            discord_avatar: Discord avatar hash

        Returns:
            User: The existing or newly created user
        """
        user = await self.user_repository.get_by_discord_id(discord_id)

        if user:
            # Update user information if it has changed
            updated = False
            if user.discord_username != discord_username:
                user.discord_username = discord_username
                updated = True
            if (
                discord_discriminator
                and user.discord_discriminator != discord_discriminator
            ):
                user.discord_discriminator = discord_discriminator
                updated = True
            if discord_avatar and user.discord_avatar != discord_avatar:
                user.discord_avatar = discord_avatar
                updated = True

            if updated:
                await user.save()

            return user

        # Create new user with default USER permission
        user = await self.user_repository.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=discord_discriminator,
            discord_avatar=discord_avatar,
            permission=Permission.USER,
        )

        # Emit user created event
        event = UserCreatedEvent(
            entity_id=user.id,
            user_id=SYSTEM_USER_ID,  # System/OAuth action
            organization_id=None,  # Not org-specific
            discord_id=discord_id,
            discord_username=discord_username,
        )
        await EventBus.emit(event)
        logger.debug("Emitted UserCreatedEvent for user %s", user.id)

        return user

    async def create_user_manual(
        self,
        discord_id: int,
        discord_username: str,
        discord_email: Optional[str] = None,
        permission: Permission = Permission.USER,
        is_active: bool = True,
        discord_discriminator: Optional[str] = None,
        discord_avatar: Optional[str] = None,
    ) -> User:
        """Create a user manually.

        Validates uniqueness by Discord ID and applies defaults consistent with
        OAuth-created users.

        Args:
            discord_id: Discord user ID (unique)
            discord_username: Display username
            discord_email: Optional email
            permission: Initial permission level (default USER)
            is_active: Whether the account is active (default True)
            discord_discriminator: Optional discriminator (legacy)
            discord_avatar: Optional avatar hash

        Returns:
            User: The newly created user

        Raises:
            ValueError: If a user with the given Discord ID already exists
        """
        # Ensure required fields
        if not discord_id or not discord_username:
            raise ValueError("discord_id and discord_username are required")

        existing = await self.user_repository.get_by_discord_id(discord_id)
        if existing:
            raise ValueError("A user with this Discord ID already exists")

        # Create via repository; default is_active True, override if specified
        user = await self.user_repository.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=discord_discriminator,
            discord_avatar=discord_avatar,
            permission=permission,
        )

        if user.is_active != is_active:
            user.is_active = is_active
            await user.save()

        # Emit user created event
        event = UserCreatedEvent(
            entity_id=user.id,
            user_id=None,  # Manual creation, could be admin
            organization_id=None,  # Not org-specific
            discord_id=discord_id,
            discord_username=discord_username,
        )
        await EventBus.emit(event)
        logger.debug("Emitted UserCreatedEvent for manually created user %s", user.id)

        return user

    async def update_user_permission(
        self,
        user_id: int,
        new_permission: Permission,
        acting_user_id: Optional[int] = None,
    ) -> User:
        """
        Update a user's permission level.

        Args:
            user_id: ID of the user to update
            new_permission: New permission level
            acting_user_id: ID of user performing the action (for audit)

        Returns:
            User: Updated user

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        old_permission = user.permission
        user.permission = new_permission
        await user.save()

        # Emit permission changed event
        event = UserPermissionChangedEvent(
            entity_id=user.id,
            user_id=acting_user_id,
            organization_id=None,  # Global permission change
            old_permission=old_permission.name,
            new_permission=new_permission.name,
        )
        await EventBus.emit(event)
        logger.debug(
            "Emitted UserPermissionChangedEvent for user %s: %s -> %s",
            user.id,
            old_permission.name,
            new_permission.name,
        )

        return user

    async def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate a user account.

        Args:
            user_id: ID of the user to deactivate

        Returns:
            User: Deactivated user

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        user.is_active = False
        await user.save()

        return user

    async def activate_user(self, user_id: int) -> User:
        """
        Activate a user account.

        Args:
            user_id: ID of the user to activate

        Returns:
            User: Activated user

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        user.is_active = True
        await user.save()

        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by their ID.

        Args:
            user_id: ID of the user to retrieve

        Returns:
            User: The user if found, None otherwise
        """
        return await self.user_repository.get_by_id(user_id)

    async def get_all_users(
        self, current_user: Optional[User], include_inactive: bool = False
    ) -> list[User]:
        """
        Get all users (requires ADMIN permission).

        Args:
            current_user: User performing the action
            include_inactive: Whether to include inactive users

        Returns:
            list[User]: List of users (empty list if unauthorized)
        """
        # Check authorization
        if not current_user or not current_user.has_permission(Permission.ADMIN):
            logger.warning(
                "Unauthorized get_all_users attempt by user %s",
                getattr(current_user, "id", None),
            )
            return []

        return await self.user_repository.get_all(include_inactive=include_inactive)

    async def search_users(
        self, current_user: Optional[User], query: str
    ) -> list[User]:
        """
        Search users by username (requires MODERATOR permission).

        Args:
            current_user: User performing the action
            query: Search query

        Returns:
            list[User]: List of matching users (empty list if unauthorized)
        """
        # Check authorization
        if not current_user or not current_user.has_permission(Permission.MODERATOR):
            logger.warning(
                "Unauthorized search_users attempt by user %s",
                getattr(current_user, "id", None),
            )
            return []

        return await self.user_repository.search_by_username(query)

    async def link_racetime_account(
        self,
        user: User,
        racetime_id: str,
        racetime_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> User:
        """
        Link RaceTime.gg account to a user.

        Args:
            user: User to link the account to
            racetime_id: RaceTime.gg user ID
            racetime_name: RaceTime.gg username
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token (optional)
            expires_at: Access token expiration timestamp (optional)

        Returns:
            User: Updated user with linked RaceTime account

        Raises:
            ValueError: If RaceTime account is already linked to another user
        """
        # Check if this racetime_id is already linked to a different user
        existing_user = await self.user_repository.get_by_racetime_id(racetime_id)
        if existing_user and existing_user.id != user.id:
            logger.warning(
                "RaceTime account %s already linked to user %s, attempted by user %s",
                racetime_id,
                existing_user.id,
                user.id,
            )
            raise ValueError(
                "This RaceTime.gg account is already linked to another user"
            )

        # Update user with RaceTime information
        user.racetime_id = racetime_id
        user.racetime_name = racetime_name
        user.racetime_access_token = access_token
        user.racetime_refresh_token = refresh_token
        user.racetime_token_expires_at = expires_at
        await user.save()

        logger.info("Linked RaceTime account %s to user %s", racetime_id, user.id)
        return user

    async def refresh_racetime_token(self, user: User) -> User:
        """
        Refresh RaceTime.gg access token for a user.

        Args:
            user: User with linked RaceTime account

        Returns:
            User: Updated user with refreshed token

        Raises:
            ValueError: If user has no linked account or no refresh token
            httpx.HTTPError: If token refresh fails
        """
        from middleware.racetime_oauth import RacetimeOAuthService

        if not user.racetime_id or not user.racetime_refresh_token:
            raise ValueError("User has no linked RaceTime account or refresh token")

        oauth_service = RacetimeOAuthService()
        token_response = await oauth_service.refresh_access_token(
            user.racetime_refresh_token
        )

        # Update user with new token information
        user.racetime_access_token = token_response.get("access_token")

        # Update refresh token if provided (some OAuth providers rotate refresh tokens)
        if "refresh_token" in token_response:
            user.racetime_refresh_token = token_response["refresh_token"]

        # Calculate expiration if provided
        if "expires_in" in token_response:
            user.racetime_token_expires_at = oauth_service.calculate_token_expiry(
                token_response["expires_in"]
            )

        await user.save()

        logger.info("Refreshed RaceTime token for user %s", user.id)
        return user

    async def unlink_racetime_account(self, user: User) -> User:
        """
        Unlink RaceTime.gg account from a user.

        Args:
            user: User to unlink the account from

        Returns:
            User: Updated user with unlinked RaceTime account
        """
        user.racetime_id = None
        user.racetime_name = None
        user.racetime_access_token = None
        user.racetime_refresh_token = None
        user.racetime_token_expires_at = None
        await user.save()

        logger.info("Unlinked RaceTime account from user %s", user.id)
        return user

    async def admin_unlink_racetime_account(
        self, user_id: int, admin_user: User
    ) -> Optional[User]:
        """
        Administratively unlink RaceTime.gg account from a user.

        Args:
            user_id: ID of user to unlink
            admin_user: Admin user performing the action

        Returns:
            Optional[User]: Updated user if successful, None if unauthorized or not found
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to admin unlink RaceTime account without permission",
                getattr(admin_user, "id", None),
            )
            return None

        # Get target user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning("User %s not found for admin unlink", user_id)
            return None

        # Unlink account
        await self.unlink_racetime_account(user)

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_unlink_racetime_account",
            details={
                "target_user_id": user_id,
                "racetime_id": user.racetime_id,
                "racetime_name": user.racetime_name,
            },
        )

        logger.info(
            "Admin %s unlinked RaceTime account for user %s", admin_user.id, user_id
        )
        return user

    async def update_discord_tokens(
        self, user: User, access_token: str, refresh_token: str, expires_at: datetime
    ) -> User:
        """
        Update Discord OAuth2 tokens for a user.

        Args:
            user: User to update tokens for
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token
            expires_at: Access token expiration timestamp

        Returns:
            User: Updated user with new tokens
        """
        user.discord_access_token = access_token
        user.discord_refresh_token = refresh_token
        user.discord_token_expires_at = expires_at
        await user.save()

        logger.info("Updated Discord tokens for user %s", user.id)
        return user

    async def refresh_discord_token(self, user: User) -> User:
        """
        Refresh Discord access token for a user.

        Args:
            user: User with Discord OAuth2 tokens

        Returns:
            User: Updated user with refreshed token

        Raises:
            ValueError: If user has no refresh token
            httpx.HTTPError: If token refresh fails
        """
        from middleware.auth import DiscordAuthService

        if not user.discord_refresh_token:
            raise ValueError("User has no Discord refresh token")

        auth_service = DiscordAuthService()
        token_response = await auth_service.refresh_discord_token(
            user.discord_refresh_token
        )

        # Update user with new token information
        user.discord_access_token = token_response.get("access_token")

        # Update refresh token if provided (Discord rotates refresh tokens)
        if "refresh_token" in token_response:
            user.discord_refresh_token = token_response["refresh_token"]

        # Calculate expiration if provided
        if "expires_in" in token_response:
            expires_at = DiscordAuthService.calculate_token_expiry(
                token_response["expires_in"]
            )
            user.discord_token_expires_at = expires_at

        await user.save()

        logger.info("Refreshed Discord token for user %s", user.id)
        return user

    async def get_all_racetime_accounts(
        self, admin_user: User, limit: Optional[int] = None, offset: int = 0
    ) -> list[User]:
        """
        Get all users with linked RaceTime accounts (admin only).

        Args:
            admin_user: Admin user requesting the data
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            list[User]: List of users with RaceTime accounts (empty if unauthorized)
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to view RaceTime accounts without permission",
                getattr(admin_user, "id", None),
            )
            return []

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_view_racetime_accounts",
            details={"limit": limit, "offset": offset},
        )

        return await self.user_repository.get_users_with_racetime(
            include_inactive=False, limit=limit, offset=offset
        )

    async def search_racetime_accounts(
        self, admin_user: User, query: str
    ) -> list[User]:
        """
        Search users by RaceTime username (admin only).

        Args:
            admin_user: Admin user performing the search
            query: Search query

        Returns:
            list[User]: List of matching users (empty if unauthorized)
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to search RaceTime accounts without permission",
                getattr(admin_user, "id", None),
            )
            return []

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_search_racetime_accounts",
            details={"query": query},
        )

        return await self.user_repository.search_by_racetime_name(query)

    async def get_racetime_link_statistics(self, admin_user: User) -> dict:
        """
        Get statistics about RaceTime account linking (admin only).

        Args:
            admin_user: Admin user requesting the stats

        Returns:
            dict: Statistics including total users, linked users, etc.
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to view RaceTime stats without permission",
                getattr(admin_user, "id", None),
            )
            return {}

        # Get statistics
        total_users = await self.user_repository.count_active_users()
        linked_users = await self.user_repository.count_racetime_linked_users(
            include_inactive=False
        )
        link_percentage = (linked_users / total_users * 100) if total_users > 0 else 0

        stats = {
            "total_users": total_users,
            "linked_users": linked_users,
            "unlinked_users": total_users - linked_users,
            "link_percentage": round(link_percentage, 2),
        }

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user, action="admin_view_racetime_stats", details=stats
        )

        logger.info("Admin %s viewed RaceTime link statistics", admin_user.id)
        return stats

    async def link_twitch_account(
        self,
        user: User,
        twitch_id: str,
        twitch_name: str,
        twitch_display_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> User:
        """
        Link Twitch account to a user.

        Args:
            user: User to link the account to
            twitch_id: Twitch user ID
            twitch_name: Twitch username (lowercase)
            twitch_display_name: Twitch display name (with capitalization)
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token (optional)
            expires_at: Access token expiration timestamp (optional)

        Returns:
            User: Updated user with linked Twitch account

        Raises:
            ValueError: If Twitch account is already linked to another user
        """
        # Check if this twitch_id is already linked to a different user
        existing_user = await self.user_repository.get_by_twitch_id(twitch_id)
        if existing_user and existing_user.id != user.id:
            logger.warning(
                "Twitch account %s already linked to user %s, attempted by user %s",
                twitch_id,
                existing_user.id,
                user.id,
            )
            raise ValueError("This Twitch account is already linked to another user")

        # Update user with Twitch information
        user.twitch_id = twitch_id
        user.twitch_name = twitch_name
        user.twitch_display_name = twitch_display_name
        user.twitch_access_token = access_token
        user.twitch_refresh_token = refresh_token
        user.twitch_token_expires_at = expires_at
        await user.save()

        logger.info("Linked Twitch account %s to user %s", twitch_id, user.id)
        return user

    async def refresh_twitch_token(self, user: User) -> User:
        """
        Refresh Twitch access token for a user.

        Args:
            user: User with linked Twitch account

        Returns:
            User: Updated user with refreshed token

        Raises:
            ValueError: If user has no linked account or no refresh token
            httpx.HTTPError: If token refresh fails
        """
        from middleware.twitch_oauth import TwitchOAuthService

        if not user.twitch_id or not user.twitch_refresh_token:
            raise ValueError("User has no linked Twitch account or refresh token")

        oauth_service = TwitchOAuthService()
        token_response = await oauth_service.refresh_access_token(
            user.twitch_refresh_token
        )

        # Update user with new token information
        user.twitch_access_token = token_response.get("access_token")

        # Update refresh token if provided (some OAuth providers rotate refresh tokens)
        if "refresh_token" in token_response:
            user.twitch_refresh_token = token_response["refresh_token"]

        # Calculate expiration if provided
        if "expires_in" in token_response:
            user.twitch_token_expires_at = oauth_service.calculate_token_expiry(
                token_response["expires_in"]
            )

        await user.save()

        logger.info("Refreshed Twitch token for user %s", user.id)
        return user

    async def unlink_twitch_account(self, user: User) -> User:
        """
        Unlink Twitch account from a user.

        Args:
            user: User to unlink the account from

        Returns:
            User: Updated user with unlinked Twitch account
        """
        user.twitch_id = None
        user.twitch_name = None
        user.twitch_display_name = None
        user.twitch_access_token = None
        user.twitch_refresh_token = None
        user.twitch_token_expires_at = None
        await user.save()

        logger.info("Unlinked Twitch account from user %s", user.id)
        return user

    async def admin_unlink_twitch_account(
        self, user_id: int, admin_user: User
    ) -> Optional[User]:
        """
        Administratively unlink Twitch account from a user.

        Args:
            user_id: ID of user to unlink
            admin_user: Admin user performing the action

        Returns:
            Optional[User]: Updated user if successful, None if unauthorized or not found
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to admin unlink Twitch account without permission",
                getattr(admin_user, "id", None),
            )
            return None

        # Get target user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning("User %s not found for admin unlink", user_id)
            return None

        # Capture Twitch info before unlinking
        twitch_id = user.twitch_id
        twitch_name = user.twitch_name

        # Unlink account
        await self.unlink_twitch_account(user)

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_unlink_twitch_account",
            details={
                "target_user_id": user_id,
                "twitch_id": twitch_id,
                "twitch_name": twitch_name,
            },
        )

        logger.info(
            "Admin %s unlinked Twitch account for user %s", admin_user.id, user_id
        )
        return user

    async def get_all_twitch_accounts(
        self, admin_user: User, limit: Optional[int] = None, offset: int = 0
    ) -> list[User]:
        """
        Get all users with linked Twitch accounts (admin only).

        Args:
            admin_user: Admin user requesting the data
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            list[User]: List of users with Twitch accounts (empty if unauthorized)
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to view Twitch accounts without permission",
                getattr(admin_user, "id", None),
            )
            return []

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_view_twitch_accounts",
            details={"limit": limit, "offset": offset},
        )

        return await self.user_repository.get_users_with_twitch(
            include_inactive=False, limit=limit, offset=offset
        )

    async def search_twitch_accounts(self, admin_user: User, query: str) -> list[User]:
        """
        Search users by Twitch username (admin only).

        Args:
            admin_user: Admin user performing the search
            query: Search query

        Returns:
            list[User]: List of matching users (empty if unauthorized)
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to search Twitch accounts without permission",
                getattr(admin_user, "id", None),
            )
            return []

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_search_twitch_accounts",
            details={"query": query},
        )

        return await self.user_repository.search_by_twitch_name(query)

    async def get_twitch_link_statistics(self, admin_user: User) -> dict:
        """
        Get statistics about Twitch account linking (admin only).

        Args:
            admin_user: Admin user requesting the stats

        Returns:
            dict: Statistics including total users, linked users, etc.
        """
        # Check admin permissions
        if not admin_user or not admin_user.has_permission(Permission.ADMIN):
            logger.warning(
                "User %s attempted to view Twitch stats without permission",
                getattr(admin_user, "id", None),
            )
            return {}

        # Get statistics
        total_users = await self.user_repository.count_active_users()
        linked_users = await self.user_repository.count_twitch_linked_users(
            include_inactive=False
        )
        link_percentage = (linked_users / total_users * 100) if total_users > 0 else 0

        stats = {
            "total_users": total_users,
            "linked_users": linked_users,
            "unlinked_users": total_users - linked_users,
            "link_percentage": round(link_percentage, 2),
        }

        # Audit log
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user, action="admin_view_twitch_stats", details=stats
        )

        logger.info("Admin %s viewed Twitch link statistics", admin_user.id)
        return stats

    async def update_user_profile(
        self,
        user: User,
        display_name: Optional[str] = None,
        pronouns: Optional[str] = None,
        show_pronouns: Optional[bool] = None,
    ) -> User:
        """
        Update a user's profile settings.

        Args:
            user: User to update
            display_name: New display name (None to leave unchanged, empty string to clear)
            pronouns: New pronouns (None to leave unchanged, empty string to clear)
            show_pronouns: Whether to show pronouns (None to leave unchanged)

        Returns:
            User: Updated user
        """
        if display_name is not None:
            user.display_name = display_name.strip() if display_name else None

        if pronouns is not None:
            user.pronouns = pronouns.strip() if pronouns else None

        if show_pronouns is not None:
            user.show_pronouns = show_pronouns

        await user.save()
        logger.info("Updated profile for user %s", user.id)
        return user

    async def start_impersonation(
        self, admin_user: User, target_user_id: int, ip_address: Optional[str] = None
    ) -> Optional[User]:
        """
        Start impersonating another user.

        Only SUPERADMIN users can impersonate others.
        Cannot impersonate yourself.
        All impersonation actions are audit logged.

        Args:
            admin_user: Admin user starting the impersonation
            target_user_id: ID of user to impersonate
            ip_address: IP address of the admin

        Returns:
            User: Target user to impersonate, or None if unauthorized
        """
        # Only SUPERADMIN can impersonate
        if not admin_user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "User %s attempted to impersonate without SUPERADMIN permission",
                admin_user.id,
            )
            return None

        # Cannot impersonate yourself
        if admin_user.id == target_user_id:
            logger.warning("User %s attempted to impersonate themselves", admin_user.id)
            return None

        # Get target user
        target_user = await self.user_repository.get_by_id(target_user_id)
        if not target_user:
            logger.warning(
                "User %s attempted to impersonate non-existent user %s",
                admin_user.id,
                target_user_id,
            )
            return None

        # Audit log the impersonation start
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="impersonation_started",
            details={
                "target_user_id": target_user.id,
                "target_username": target_user.discord_username,
                "target_permission": target_user.permission.name,
            },
            ip_address=ip_address,
        )

        logger.info(
            "User %s (SUPERADMIN) started impersonating user %s",
            admin_user.id,
            target_user.id,
        )

        return target_user

    async def stop_impersonation(
        self,
        original_user: User,
        impersonated_user: User,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Stop impersonating and return to original user.

        Audit logs the end of impersonation.

        Args:
            original_user: Original admin user
            impersonated_user: User that was being impersonated
            ip_address: IP address of the admin
        """
        # Audit log the impersonation stop
        from application.services.core.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            user=original_user,
            action="impersonation_stopped",
            details={
                "impersonated_user_id": impersonated_user.id,
                "impersonated_username": impersonated_user.discord_username,
            },
            ip_address=ip_address,
        )

        logger.info(
            "User %s stopped impersonating user %s",
            original_user.id,
            impersonated_user.id,
        )
