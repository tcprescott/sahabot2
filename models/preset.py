"""
Preset models.

This module defines the database models for presets and preset namespaces.
Presets are stored globally (not organization-scoped) and support namespacing
for different users/groups.
"""

from tortoise import fields
from tortoise.models import Model


class PresetNamespace(Model):
    """
    A namespace for organizing presets.

    Namespaces allow users to organize their presets and avoid naming conflicts.
    Examples: 'official', 'username', 'league', etc.
    """

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True, index=True)
    owner_discord_id = fields.BigIntField(null=True, index=True)
    is_public = fields.BooleanField(default=True)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Relations
    collaborators = fields.ManyToManyField(
        "models.User",
        related_name="preset_namespaces",
        through="preset_namespace_collaborators"
    )

    class Meta:
        """Meta options for PresetNamespace."""
        table = "preset_namespaces"

    def __str__(self):
        """String representation."""
        return f"PresetNamespace({self.name})"


class Preset(Model):
    """
    A preset configuration for a randomizer.

    Presets contain YAML configuration for various randomizers (ALTTPR, SMZ3, etc).
    They are organized into namespaces and can be shared globally.
    """

    id = fields.IntField(pk=True)
    preset_name = fields.CharField(max_length=255, index=True)
    randomizer = fields.CharField(max_length=50, index=True)
    namespace = fields.ForeignKeyField(
        "models.PresetNamespace",
        related_name="presets",
        on_delete=fields.CASCADE
    )
    content = fields.TextField()
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        """Meta options for Preset."""
        table = "presets"
        unique_together = (("preset_name", "randomizer", "namespace"),)
        indexes = [
            ("preset_name", "randomizer", "namespace"),
            ("randomizer", "namespace"),
        ]

    def __str__(self):
        """String representation."""
        return f"Preset({self.namespace.name}/{self.preset_name})"
