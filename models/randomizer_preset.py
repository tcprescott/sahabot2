"""
Randomizer preset database model.

This module defines the database model for storing user-created randomizer presets.
Presets are YAML configurations for randomizer settings that can be reused across
multiple seed generations.
"""

from tortoise import fields
from tortoise.models import Model


class RandomizerPreset(Model):
    """
    Model for storing global randomizer presets.

    Presets are user-created YAML configurations for randomizer settings.
    They are globally accessible to all users.

    Attributes:
        id: Primary key
        user: User who created the preset
        randomizer: Randomizer type (alttpr, sm, smz3, ootr, etc.)
        name: User-friendly name for the preset
        description: Optional description of what the preset does
        settings: YAML content as JSON (the actual preset configuration)
        is_public: Whether the preset is visible to all users
        created_at: When the preset was created
        updated_at: When the preset was last modified
    """

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='presets')
    randomizer = fields.CharField(50, description="Randomizer type (alttpr, sm, smz3, etc.)")
    name = fields.CharField(100, description="User-friendly preset name")
    description = fields.TextField(null=True, description="Optional preset description")
    settings = fields.JSONField(description="YAML preset content stored as JSON")
    is_public = fields.BooleanField(default=False, description="Visible to all users")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "randomizer_presets"
        unique_together = (("randomizer", "name"),)
        indexes = (
            ("randomizer", "user_id"),
            ("is_public",),
        )

    def __str__(self):
        """Return string representation of preset."""
        return f"{self.randomizer}/{self.name}"

    @property
    def full_name(self) -> str:
        """Return fully qualified preset name."""
        return f"{self.randomizer}/{self.name}"
