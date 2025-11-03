"""
Randomizer preset model.

This model stores preset configurations for various randomizers.
"""

from tortoise import fields
from tortoise.models import Model


class RandomizerPreset(Model):
    """
    Model for storing randomizer preset configurations.

    A preset is a named collection of settings for a specific randomizer
    (e.g., ALTTPR, SM, SMZ3). Presets are scoped to organizations to support
    multi-tenancy.

    Attributes:
        id: Primary key
        organization: Foreign key to Organization (tenant isolation)
        name: Human-readable name for the preset
        randomizer: Type of randomizer (alttpr, sm, smz3, etc.)
        settings: JSON field containing the preset settings
        description: Optional description of the preset
        is_active: Whether this preset is currently active/available
        created_at: Timestamp when preset was created
        updated_at: Timestamp when preset was last updated
    """

    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        'models.Organization',
        related_name='randomizer_presets',
        on_delete=fields.CASCADE,
        description="Organization that owns this preset"
    )
    name = fields.CharField(
        max_length=100,
        description="Human-readable name for the preset"
    )
    randomizer = fields.CharField(
        max_length=50,
        description="Type of randomizer (alttpr, sm, smz3, etc.)"
    )
    settings = fields.JSONField(
        description="JSON object containing preset settings"
    )
    description = fields.TextField(
        null=True,
        description="Optional description of the preset"
    )
    is_active = fields.BooleanField(
        default=True,
        description="Whether this preset is currently active"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "randomizer_presets"
        indexes = [
            ("organization", "randomizer"),
            ("organization", "name"),
        ]
        unique_together = (("organization", "name"),)

    def __str__(self) -> str:
        """String representation of the preset."""
        return f"{self.name} ({self.randomizer})"
