"""
User service for user-related business logic.

This module contains all business logic related to user management.
"""

import logging
import secrets
from datetime import datetime, timezone
from models import User, Permission, SYSTEM_USER_ID
from typing import Optional
from application.repositories.user_repository import UserRepository
from application.services.authorization_service import AuthorizationService
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
        discord_avatar: Optional[str] = None
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
            if discord_discriminator and user.discord_discriminator != discord_discriminator:
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
            permission=Permission.USER
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
        acting_user_id: Optional[int] = None
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
            new_permission.name
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

    async def get_all_users(self, current_user: Optional[User], include_inactive: bool = False) -> list[User]:
        """
        Get all users (requires ADMIN permission).

        Args:
            current_user: User performing the action
            include_inactive: Whether to include inactive users

        Returns:
            list[User]: List of users (empty list if unauthorized)
        """
        # Check authorization
        if not AuthorizationService.can_access_admin_panel(current_user):
            logger.warning("Unauthorized get_all_users attempt by user %s", getattr(current_user, 'id', None))
            return []
        
        return await self.user_repository.get_all(include_inactive=include_inactive)

    async def search_users(self, current_user: Optional[User], query: str) -> list[User]:
        """
        Search users by username (requires MODERATOR permission).

        Args:
            current_user: User performing the action
            query: Search query

        Returns:
            list[User]: List of matching users (empty list if unauthorized)
        """
        # Check authorization
        if not AuthorizationService.can_moderate(current_user):
            logger.warning("Unauthorized search_users attempt by user %s", getattr(current_user, 'id', None))
            return []
        
        return await self.user_repository.search_by_username(query)

    async def link_racetime_account(
        self,
        user: User,
        racetime_id: str,
        racetime_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
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
                user.id
            )
            raise ValueError("This RaceTime.gg account is already linked to another user")

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
        token_response = await oauth_service.refresh_access_token(user.racetime_refresh_token)

        # Update user with new token information
        user.racetime_access_token = token_response.get('access_token')
        
        # Update refresh token if provided (some OAuth providers rotate refresh tokens)
        if 'refresh_token' in token_response:
            user.racetime_refresh_token = token_response['refresh_token']
        
        # Calculate expiration if provided
        if 'expires_in' in token_response:
            user.racetime_token_expires_at = oauth_service.calculate_token_expiry(
                token_response['expires_in']
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
        self,
        user_id: int,
        admin_user: User
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
        auth_service = AuthorizationService()
        if not auth_service.can_access_admin_panel(admin_user):
            logger.warning(
                "User %s attempted to admin unlink RaceTime account without permission",
                admin_user.id
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
        from application.services.audit_service import AuditService
        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_unlink_racetime_account",
            details={
                "target_user_id": user_id,
                "racetime_id": user.racetime_id,
                "racetime_name": user.racetime_name
            }
        )

        logger.info(
            "Admin %s unlinked RaceTime account for user %s",
            admin_user.id,
            user_id
        )
        return user

    async def get_all_racetime_accounts(
        self,
        admin_user: User,
        limit: Optional[int] = None,
        offset: int = 0
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
        auth_service = AuthorizationService()
        if not auth_service.can_access_admin_panel(admin_user):
            logger.warning(
                "User %s attempted to view RaceTime accounts without permission",
                admin_user.id
            )
            return []

        # Audit log
        from application.services.audit_service import AuditService
        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_view_racetime_accounts",
            details={"limit": limit, "offset": offset}
        )

        return await self.user_repository.get_users_with_racetime(
            include_inactive=False,
            limit=limit,
            offset=offset
        )

    async def search_racetime_accounts(
        self,
        admin_user: User,
        query: str
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
        auth_service = AuthorizationService()
        if not auth_service.can_access_admin_panel(admin_user):
            logger.warning(
                "User %s attempted to search RaceTime accounts without permission",
                admin_user.id
            )
            return []

        # Audit log
        from application.services.audit_service import AuditService
        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_search_racetime_accounts",
            details={"query": query}
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
        auth_service = AuthorizationService()
        if not auth_service.can_access_admin_panel(admin_user):
            logger.warning(
                "User %s attempted to view RaceTime stats without permission",
                admin_user.id
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
            "link_percentage": round(link_percentage, 2)
        }

        # Audit log
        from application.services.audit_service import AuditService
        audit_service = AuditService()
        await audit_service.log_action(
            user=admin_user,
            action="admin_view_racetime_stats",
            details=stats
        )

        logger.info("Admin %s viewed RaceTime link statistics", admin_user.id)
        return stats

    async def update_user_profile(
        self,
        user: User,
        display_name: Optional[str] = None,
        pronouns: Optional[str] = None,
        show_pronouns: Optional[bool] = None
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

    async def update_user_email(
        self,
        user: User,
        email: Optional[str]
    ) -> User:
        """
        Update a user's email address.

        Note: Email verification is currently stubbed - emails are automatically marked as verified.
        This is a placeholder for future email verification implementation.

        Args:
            user: User to update
            email: New email address (None or empty string to clear)

        Returns:
            User: Updated user

        Raises:
            ValueError: If email format is invalid
        """
        # Normalize email
        normalized_email = email.strip().lower() if email else None

        # Basic email validation
        if normalized_email:
            if '@' not in normalized_email or '.' not in normalized_email.split('@')[-1]:
                raise ValueError("Invalid email format")

        # Clear email if None or empty
        if not normalized_email:
            user.email = None
            user.email_verified = False
            user.email_verification_token = None
            user.email_verified_at = None
            await user.save()
            logger.info("Cleared email for user %s", user.id)
            return user

        # Update email
        user.email = normalized_email

        # STUBBED: Auto-verify email without sending verification email
        # TODO: Implement proper email verification flow with email provider
        user.email_verified = True
        user.email_verification_token = None
        user.email_verified_at = datetime.now(timezone.utc)

        await user.save()
        logger.info("Updated and auto-verified email for user %s", user.id)
        return user

    async def initiate_email_verification(
        self,
        user: User
    ) -> str:
        """
        Initiate email verification process.

        Note: This is currently stubbed and auto-verifies the email.
        In the future, this will send a verification email.

        Args:
            user: User to verify email for

        Returns:
            str: Verification token (for future use)

        Raises:
            ValueError: If user has no email set
        """
        if not user.email:
            raise ValueError("User has no email address set")

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # STUBBED: In production, we would:
        # 1. Store the token
        # 2. Send verification email
        # 3. Wait for user to click link
        # For now, just auto-verify
        user.email_verification_token = None  # Don't store token since we auto-verify
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        await user.save()

        logger.info("Auto-verified email for user %s (verification stubbed)", user.id)
        return verification_token

    async def verify_email(
        self,
        user: User,
        verification_token: str
    ) -> bool:
        """
        Verify user's email with token.

        Note: This is currently stubbed. In production, this would validate the token.

        Args:
            user: User to verify
            verification_token: Token from verification email

        Returns:
            bool: True if verification successful
        """
        # STUBBED: Always return True since we auto-verify
        if not user.email_verified:
            user.email_verified = True
            user.email_verified_at = datetime.now(timezone.utc)
            user.email_verification_token = None
            await user.save()
            logger.info("Verified email for user %s", user.id)

        return True
