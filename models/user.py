"""
User model and permission definitions.

This module contains the User model and Permission enum for authentication and authorization.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model
from enum import IntEnum

if TYPE_CHECKING:
    from .api_token import ApiToken
    from .audit_log import AuditLog
    from .match_schedule import MatchPlayers, TournamentPlayers, Crew
    from .organizations import OrganizationMember


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
        discord_id: Discord user ID (unique)
        discord_username: Discord username
        discord_discriminator: Discord discriminator (deprecated by Discord but kept for compatibility)
        discord_avatar: Discord avatar hash
        discord_email: Discord email address
        racetime_id: RaceTime.gg user ID (unique, nullable)
        racetime_name: RaceTime.gg username (nullable)
        racetime_access_token: OAuth2 access token for RaceTime.gg API (nullable)
        permission: User permission level
        is_active: Whether the user account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    id = fields.IntField(pk=True)
    discord_id = fields.BigIntField(unique=True, index=True)
    discord_username = fields.CharField(max_length=255)
    discord_discriminator = fields.CharField(max_length=4, null=True)
    discord_avatar = fields.CharField(max_length=255, null=True)
    discord_email = fields.CharField(max_length=255, null=True)

    # RaceTime.gg account linking
    racetime_id = fields.CharField(max_length=255, null=True, unique=True, index=True)
    racetime_name = fields.CharField(max_length=255, null=True)
    racetime_access_token = fields.TextField(null=True)

    permission = fields.IntEnumField(Permission, default=Permission.USER)
    is_active = fields.BooleanField(default=True)
    # Optional per-user API rate limit (requests per minute). If null, use default from settings.
    api_rate_limit_per_minute = fields.IntField(null=True)

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

    class Meta:
        table = "users"

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
