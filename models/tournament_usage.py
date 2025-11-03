"""
Tournament usage tracking model.

This module tracks which tournaments users have recently accessed
to provide quick access links on the home page.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .user import User
    from .match_schedule import Tournament


class TournamentUsage(Model):
    """
    Track user's tournament access for recent tournament history.

    Attributes:
        id: Primary key
        user: User who accessed the tournament
        tournament: Tournament that was accessed
        last_accessed: Timestamp of most recent access
        organization_id: Organization ID for the tournament (denormalized for performance)
        organization_name: Organization name (denormalized for performance)
        tournament_name: Tournament name (denormalized for performance)
    """

    id = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="tournament_usage", on_delete=fields.CASCADE, index=True
    )
    tournament: fields.ForeignKeyRelation[Tournament] = fields.ForeignKeyField(
        "models.Tournament", related_name="usage_tracking", on_delete=fields.CASCADE
    )
    last_accessed = fields.DatetimeField(auto_now=True, index=True)

    # Denormalized fields for efficient querying without joins
    organization_id = fields.IntField()
    organization_name = fields.CharField(max_length=255)
    tournament_name = fields.CharField(max_length=255)

    class Meta:
        table = "tournament_usage"
        unique_together = (("user", "tournament"),)
        indexes = (
            ("user_id", "last_accessed"),  # For fetching recent tournaments by user
        )

    def __str__(self) -> str:
        """String representation of tournament usage."""
        return f"{self.user.discord_username} - {self.tournament_name} ({self.last_accessed})"
