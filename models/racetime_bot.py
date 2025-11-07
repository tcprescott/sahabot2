"""
RaceTime Bot models.

Models for managing racetime.gg bot instances and their organization assignments.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from enum import IntEnum
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .organizations import Organization


class BotStatus(IntEnum):
    """Status of a RaceTime bot connection."""
    UNKNOWN = 0  # Not yet connected or status not checked
    CONNECTED = 1  # Successfully connected and authenticated
    AUTH_FAILED = 2  # Authentication failed (invalid credentials)
    CONNECTION_ERROR = 3  # Network or connection error
    DISCONNECTED = 4  # Intentionally disconnected or stopped


class RacetimeBot(Model):
    """
    RaceTime bot configuration.

    Stores OAuth2 credentials for racetime.gg bot instances.
    Bots are global (not organization-scoped) but can be assigned to organizations.
    """
    id = fields.IntField(pk=True)
    category = fields.CharField(max_length=50, unique=True, description="RaceTime category slug (e.g., 'alttpr', 'smz3')")
    client_id = fields.CharField(max_length=255, description="OAuth2 client ID")
    client_secret = fields.CharField(max_length=255, description="OAuth2 client secret")
    name = fields.CharField(max_length=255, description="Friendly name for this bot")
    description = fields.TextField(null=True, description="Optional description")
    is_active = fields.BooleanField(default=True, description="Whether this bot is enabled")
    handler_class = fields.CharField(
        max_length=255,
        default='SahaRaceHandler',
        description="Python class name for the race handler (e.g., 'ALTTPRRaceHandler', 'SMRaceHandler', 'SMZ3RaceHandler')"
    )
    
    # Status tracking
    status = fields.IntEnumField(BotStatus, default=BotStatus.UNKNOWN, description="Current connection status")
    status_message = fields.TextField(null=True, description="Additional status information or error message")
    last_connected_at = fields.DatetimeField(null=True, description="Timestamp of last successful connection")
    last_status_check_at = fields.DatetimeField(null=True, description="Timestamp of last status check")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Reverse relations
    organization_assignments: fields.ReverseRelation["RacetimeBotOrganization"]

    class Meta:
        table = "racetime_bots"

    def __str__(self) -> str:
        return f"{self.name} ({self.category})"
    
    def get_status_display(self) -> str:
        """Get human-readable status."""
        status_map = {
            BotStatus.UNKNOWN: "Unknown",
            BotStatus.CONNECTED: "Connected",
            BotStatus.AUTH_FAILED: "Authentication Failed",
            BotStatus.CONNECTION_ERROR: "Connection Error",
            BotStatus.DISCONNECTED: "Disconnected",
        }
        return status_map.get(self.status, "Unknown")
    
    def is_healthy(self) -> bool:
        """Check if bot is in a healthy state."""
        return self.status == BotStatus.CONNECTED


class RacetimeBotOrganization(Model):
    """
    Assignment of a RaceTime bot to an organization.

    Allows organizations to use specific bots for their tournaments/races.
    """
    id = fields.IntField(pk=True)
    bot = fields.ForeignKeyField('models.RacetimeBot', related_name='organization_assignments')
    organization = fields.ForeignKeyField('models.Organization', related_name='racetime_bots')
    is_active = fields.BooleanField(default=True, description="Whether this assignment is active")
    assigned_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "racetime_bot_organizations"
        unique_together = (("bot", "organization"),)

    def __str__(self) -> str:
        return f"{self.bot.category} → {self.organization.name}"
