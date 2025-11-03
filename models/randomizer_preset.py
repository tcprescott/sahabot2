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
    Model for storing randomizer presets.

    Presets are user-created YAML configurations for randomizer settings.
    They are organized into namespaces (user or organization owned).

    Attributes:
        id: Primary key
        namespace: Namespace this preset belongs to
        user: User who created the preset (for tracking creator)
        randomizer: Randomizer type (alttpr, sm, smz3, ootr, etc.)
        name: User-friendly name for the preset (unique within namespace+randomizer)
        description: Optional description of what the preset does
        settings: YAML content as JSON (the actual preset configuration)
        is_public: Whether the preset is visible to all users
        created_at: When the preset was created
        updated_at: When the preset was last modified
    """

    id = fields.IntField(pk=True)
    namespace = fields.ForeignKeyField(
        'models.PresetNamespace',
        related_name='presets',
        null=True,
        description="Namespace this preset belongs to (null for global presets)"
    )
    user = fields.ForeignKeyField(
        'models.User',
        related_name='created_presets',
        description="User who created the preset"
    )
    randomizer = fields.CharField(50, description="Randomizer type (alttpr, sm, smz3, etc.)")
    name = fields.CharField(100, description="User-friendly preset name")
    description = fields.TextField(null=True, description="Optional preset description")
    settings = fields.JSONField(description="YAML preset content stored as JSON")
    is_public = fields.BooleanField(default=False, description="Visible to all users")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "randomizer_presets"
        unique_together = (
            ("namespace_id", "randomizer", "name"),  # Namespace presets must be unique
            ("randomizer", "name"),  # Global presets (namespace_id=null) must be unique
        )
        indexes = (
            ("namespace_id", "randomizer"),
            ("randomizer", "user_id"),
            ("is_public",),
        )

    def __str__(self):
        """Return string representation of preset."""
        return f"{self.randomizer}/{self.name}"

    @property
    def full_name(self) -> str:
        """Return fully qualified preset name with namespace."""
        # Will need to load namespace relationship
        return f"{self.randomizer}/{self.name}"

    @property
    def qualified_name(self) -> str:
        """Return namespace-qualified preset name."""
        # Format: namespace/randomizer/name or global/randomizer/name
        # Note: This requires namespace to be prefetched
        return f"{self.randomizer}/{self.name}"

    @property
    def is_global(self) -> bool:
        """Check if this is a global (non-namespaced) preset."""
        return self.namespace_id is None

    @property
    def scope_display(self) -> str:
        """Return display text for preset scope."""
        if self.is_global:
            return "Global"
        return "Namespace"
