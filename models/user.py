"""
User model and permission definitions.

This module contains the User model and Permission enum for authentication and authorization.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from tortoise import fields
from tortoise.models import Model
from enum import IntEnum

if TYPE_CHECKING:
    from .api_token import ApiToken
    from .audit_log import AuditLog
    from modules.tournament.models.match_schedule import (
        MatchPlayers,
        TournamentPlayers,
        Crew,
    )
    from .organizations import OrganizationMember
    from modules.tournament.models.tournament_usage import TournamentUsage
    from modules.tournament.models.tournament_match_settings import (
        TournamentMatchSettings,
    )


# Sentinel value for system/automation actions
# Use -1 to indicate automated system actions (distinct from None which means unknown/unauthenticated)
SYSTEM_USER_ID = -1


class Permission(IntEnum):
    """
    User permission levels.

    Higher values indicate higher privilege levels.
    """

    USER = 0
    MODERATOR = 50
    ADMIN = 100
    SUPERADMIN = 200


class User(Model):
    """
    User model representing Discord-authenticated users.

    Attributes:
        id: Primary key
        discord_id: Discord user ID (unique, nullable for placeholder users)
        discord_username: Discord username
        discord_discriminator: Discord discriminator (deprecated by Discord but kept for compatibility)
        discord_avatar: Discord avatar hash
        discord_email: Discord email address
        discord_access_token: OAuth2 access token for Discord API (nullable)
        discord_refresh_token: OAuth2 refresh token for Discord API (nullable)
        discord_token_expires_at: Access token expiration timestamp (nullable)
        racetime_id: RaceTime.gg user ID (unique, nullable)
        racetime_name: RaceTime.gg username (nullable)
        racetime_access_token: OAuth2 access token for RaceTime.gg API (nullable)
        racetime_refresh_token: OAuth2 refresh token for RaceTime.gg API (nullable)
        racetime_token_expires_at: Access token expiration timestamp (nullable)
        twitch_id: Twitch user ID (unique, nullable)
        twitch_name: Twitch username (lowercase, nullable)
        twitch_display_name: Twitch display name (with capitalization, nullable)
        twitch_access_token: OAuth2 access token for Twitch API (nullable)
        twitch_refresh_token: OAuth2 refresh token for Twitch API (nullable)
        twitch_token_expires_at: Access token expiration timestamp (nullable)
        display_name: User's chosen display name (falls back to discord_username if not set)
        pronouns: User's pronouns (optional)
        show_pronouns: Whether to display pronouns with the user's name
        permission: User permission level
        is_active: Whether the user account is active
        is_placeholder: True if this is a placeholder user created from SpeedGaming import
        speedgaming_id: SpeedGaming player/crew ID for placeholder users (nullable)
        created_at: Account creation timestamp
        updated_at: Last update timestamp

    Constraints:
        - discord_id can only be NULL if is_placeholder is True
        - This ensures all real users have a Discord ID, while placeholders may not
    """

    id = fields.IntField(pk=True)
    discord_id = fields.BigIntField(unique=True, index=True, null=True)
    discord_username = fields.CharField(max_length=255)
    discord_discriminator = fields.CharField(max_length=4, null=True)
    discord_avatar = fields.CharField(max_length=255, null=True)
    discord_email = fields.CharField(max_length=255, null=True)

    # Discord OAuth2 tokens for automatic refresh
    discord_access_token = fields.TextField(null=True)
    discord_refresh_token = fields.TextField(null=True)
    discord_token_expires_at = fields.DatetimeField(null=True)

    # RaceTime.gg account linking
    racetime_id = fields.CharField(max_length=255, null=True, unique=True, index=True)
    racetime_name = fields.CharField(max_length=255, null=True)
    racetime_access_token = fields.TextField(null=True)
    racetime_refresh_token = fields.TextField(null=True)
    racetime_token_expires_at = fields.DatetimeField(null=True)

    # Twitch account linking
    twitch_id = fields.CharField(max_length=255, null=True, unique=True, index=True)
    twitch_name = fields.CharField(max_length=255, null=True)
    twitch_display_name = fields.CharField(max_length=255, null=True)
    twitch_access_token = fields.TextField(null=True)
    twitch_refresh_token = fields.TextField(null=True)
    twitch_token_expires_at = fields.DatetimeField(null=True)

    # User profile preferences
    display_name = fields.CharField(max_length=255, null=True)
    pronouns = fields.CharField(max_length=100, null=True)
    show_pronouns = fields.BooleanField(default=False)

    permission = fields.IntEnumField(Permission, default=Permission.USER)
    is_active = fields.BooleanField(default=True)
    # Optional per-user API rate limit (requests per minute). If null, use default from settings.
    api_rate_limit_per_minute = fields.IntField(null=True)

    # SpeedGaming integration - track placeholder users created from SG data
    is_placeholder = fields.BooleanField(
        default=False
    )  # True if created as placeholder for SpeedGaming import
    speedgaming_id = fields.IntField(
        null=True
    )  # SpeedGaming player/crew ID for placeholder users

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # related fields (reverse relations)
    api_tokens: fields.ReverseRelation["ApiToken"]
    audit_logs: fields.ReverseRelation["AuditLog"]
    match_players: fields.ReverseRelation["MatchPlayers"]
    tournament_players: fields.ReverseRelation["TournamentPlayers"]
    crew_memberships: fields.ReverseRelation["Crew"]
    approved_crew: fields.ReverseRelation["Crew"]
    organizations: fields.ReverseRelation["OrganizationMember"]
    tournament_usage: fields.ReverseRelation["TournamentUsage"]
    tournament_settings_submissions: fields.ReverseRelation["TournamentMatchSettings"]

    class Meta:
        table = "users"
        # Constraint: discord_id can only be NULL if is_placeholder is True
        # In SQL: CHECK (discord_id IS NOT NULL OR is_placeholder = 1)
        constraints = ["CHECK (discord_id IS NOT NULL OR is_placeholder = 1)"]

    def __str__(self) -> str:
        """String representation of user."""
        return f"{self.discord_username} ({self.discord_id})"

    def has_permission(self, required_permission: Permission) -> bool:
        """
        Check if user has required permission level.

        Args:
            required_permission: Minimum required permission level

        Returns:
            bool: True if user has sufficient permissions
        """
        return self.is_active and self.permission >= required_permission

    def is_admin(self) -> bool:
        """
        Check if user has admin privileges.

        Returns:
            bool: True if user is admin or higher
        """
        return self.has_permission(Permission.ADMIN)

    def is_moderator(self) -> bool:
        """
        Check if user has moderator privileges.

        Returns:
            bool: True if user is moderator or higher
        """
        return self.has_permission(Permission.MODERATOR)

    def get_display_name(self) -> str:
        """
        Get the user's display name.

        Returns the user's chosen display name if set, otherwise falls back to discord_username.

        Returns:
            str: The display name to show in the UI
        """
        return self.display_name if self.display_name else self.discord_username

    def get_full_display_name(self) -> str:
        """
        Get the user's display name with optional pronouns.

        Returns the display name with pronouns in italics if enabled.

        Returns:
            str: Display name with pronouns if show_pronouns is True
        """
        name = self.get_display_name()
        if self.show_pronouns and self.pronouns:
            return f"{name} ({self.pronouns})"
        return name


def is_system_user_id(user_id: Optional[int]) -> bool:
    """
    Check if a user_id represents a system/automation action.

    Args:
        user_id: User ID to check

    Returns:
        bool: True if this is a system action (SYSTEM_USER_ID), False otherwise
    """
    return user_id == SYSTEM_USER_ID


def is_authenticated_user_id(user_id: Optional[int]) -> bool:
    """
    Check if a user_id represents an authenticated user.

    This returns True for any positive user ID (actual users).

    Args:
        user_id: User ID to check

    Returns:
        bool: True if this is a real user ID (> 0), False for None or SYSTEM_USER_ID
    """
    return user_id is not None and user_id > 0


def get_user_id_description(user_id: Optional[int]) -> str:
    """
    Get a human-readable description of what a user_id represents.

    Useful for logging and auditing.

    Args:
        user_id: User ID to describe

    Returns:
        str: Description of the user_id
    """
    if user_id is None:
        return "Unknown/Unauthenticated"
    elif user_id == SYSTEM_USER_ID:
        return "System/Automation"
    else:
        return f"User {user_id}"
