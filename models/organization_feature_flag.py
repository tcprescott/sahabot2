"""Organization feature flags model."""

from enum import IntEnum
from tortoise import fields
from tortoise.models import Model


class FeatureFlag(IntEnum):
    """Available feature flags for organizations."""

    LIVE_RACES = 1
    ADVANCED_PRESETS = 2
    RACETIME_BOT = 3
    SCHEDULED_TASKS = 4
    DISCORD_EVENTS = 5


class OrganizationFeatureFlag(Model):
    """
    Feature flag for enabling/disabling organization-specific features.

    Allows SUPERADMIN to selectively enable advanced features for organizations,
    preventing UI clutter for organizations that only use basic features.
    """

    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        "models.Organization", related_name="feature_flags", on_delete=fields.CASCADE
    )
    feature_key = fields.IntEnumField(FeatureFlag, description="Feature identifier")
    enabled = fields.BooleanField(
        default=False,
        description="Whether this feature is enabled for the organization",
    )
    enabled_at = fields.DatetimeField(
        null=True,
        description="When the feature was enabled (null if currently disabled)",
    )
    enabled_by = fields.ForeignKeyField(
        "models.User",
        related_name="feature_flags_enabled",
        null=True,
        on_delete=fields.SET_NULL,
        description="SUPERADMIN who enabled the feature",
    )
    notes = fields.TextField(
        null=True, description="Optional notes about why feature was enabled/disabled"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organization_feature_flags"
        unique_together = (("organization", "feature_key"),)
        indexes = [
            ("organization", "feature_key"),
            ("feature_key", "enabled"),
        ]

    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.feature_key.name} ({status}) for {self.organization.name}"
