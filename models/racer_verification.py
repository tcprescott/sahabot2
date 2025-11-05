"""
Racer Verification models.

Models for Discord role-based racer verification system.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .organizations import Organization
    from .user import User


class RacerVerification(Model):
    """
    Racer verification configuration for an organization.

    Defines requirements for users to receive a verified racer role in Discord.
    Users must have a linked RaceTime.gg account and meet minimum race requirements.
    """
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='racer_verifications')

    # Discord configuration
    guild_id = fields.BigIntField(index=True)  # Discord guild/server ID
    role_id = fields.BigIntField()  # Discord role ID to grant
    role_name = fields.CharField(max_length=255)  # Role name (for display)

    # Race requirements
    categories = fields.JSONField(default=list)  # RaceTime categories (e.g., ['alttpr', 'alttprbiweekly'])
    minimum_races = fields.IntField(default=5)  # Minimum completed races required
    count_forfeits = fields.BooleanField(default=False)  # Whether to count forfeited races
    count_dq = fields.BooleanField(default=False)  # Whether to count disqualified races

    # Status
    is_active = fields.BooleanField(default=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Reverse relations
    user_verifications: fields.ReverseRelation["UserRacerVerification"]

    class Meta:
        table = "racer_verifications"
        unique_together = [("organization", "guild_id", "role_id")]


class UserRacerVerification(Model):
    """
    Individual user's racer verification status.

    Tracks whether a user has been verified and granted the role.
    """
    id = fields.IntField(pk=True)
    verification = fields.ForeignKeyField('models.RacerVerification', related_name='user_verifications')
    user = fields.ForeignKeyField('models.User', related_name='racer_verifications')

    # Verification details
    is_verified = fields.BooleanField(default=False)
    verified_at = fields.DatetimeField(null=True)
    race_count = fields.IntField(default=0)  # Number of qualifying races at verification time
    role_granted = fields.BooleanField(default=False)  # Whether Discord role was successfully granted
    role_granted_at = fields.DatetimeField(null=True)

    # Last check
    last_checked_at = fields.DatetimeField(null=True)
    last_check_error = fields.TextField(null=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_racer_verifications"
        unique_together = [("verification", "user")]
