"""
Discord Guild (Server) models.

Models for linking Discord servers to organizations.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .organizations import Organization


class DiscordGuild(Model):
    """
    Discord Guild linked to an organization.

    Represents a Discord server that has been connected to an organization,
    allowing the bot to operate in that server with organization-specific context.
    """

    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        "models.Organization", related_name="discord_guilds"
    )

    # Discord guild information
    guild_id = fields.BigIntField(
        index=True
    )  # Discord snowflake ID (can be linked to multiple orgs)
    guild_name = fields.CharField(max_length=255)
    guild_icon = fields.CharField(max_length=255, null=True)  # Icon hash

    # Verification info
    linked_by = fields.ForeignKeyField(
        "models.User", related_name="linked_guilds"
    )  # User who linked the server
    verified_admin = fields.BooleanField(
        default=False
    )  # Whether admin permissions were verified

    # Status
    is_active = fields.BooleanField(default=True)
    bot_left_at = fields.DatetimeField(
        null=True
    )  # Track when bot was removed from server

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "discord_guilds"
        unique_together = [
            ("organization", "guild_id")
        ]  # One org can only link a guild once

    @property
    def guild_icon_url(self) -> str | None:
        """Get the full URL for the guild icon."""
        if not self.guild_icon:
            return None
        return f"https://cdn.discordapp.com/icons/{self.guild_id}/{self.guild_icon}.png"
