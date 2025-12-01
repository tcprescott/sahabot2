"""
Plugin database models.

This module defines the database models for plugin management:
- Plugin: Installation records for plugins
- OrganizationPlugin: Per-organization plugin enablement
- PluginMigration: Plugin migration tracking
"""

from enum import Enum

from tortoise import fields
from tortoise.models import Model


class PluginTypeDB(str, Enum):
    """Plugin installation type (database enum)."""

    BUILTIN = "builtin"
    EXTERNAL = "external"


class Plugin(Model):
    """
    Plugin installation record.

    Tracks which plugins are installed in the system, their versions,
    and global configuration.
    """

    id = fields.IntField(pk=True)
    plugin_id = fields.CharField(max_length=100, unique=True, description="Unique plugin identifier")
    name = fields.CharField(max_length=255, description="Display name")
    version = fields.CharField(max_length=50, description="Current version")
    type = fields.CharEnumField(PluginTypeDB, description="Plugin type (builtin/external)")
    is_installed = fields.BooleanField(default=True, description="Whether plugin is installed")
    enabled_by_default = fields.BooleanField(default=True, description="Default enabled state for new orgs")
    private = fields.BooleanField(default=False, description="Requires admin to grant org access")
    global_plugin = fields.BooleanField(default=False, description="Always enabled, not org-scoped")
    installed_at = fields.DatetimeField(null=True, description="Installation timestamp")
    installed_by = fields.ForeignKeyField(
        "models.User",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="installed_plugins",
        description="User who installed the plugin",
    )
    config = fields.JSONField(null=True, description="Global plugin configuration")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "plugins"

    def __str__(self) -> str:
        return f"Plugin({self.plugin_id}, v{self.version})"


class OrganizationPlugin(Model):
    """
    Organization-level plugin enablement.

    Tracks which plugins are enabled for each organization and
    organization-specific configuration overrides.
    """

    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField(
        "models.Organization",
        on_delete=fields.CASCADE,
        related_name="plugins",
        description="Organization this enablement applies to",
    )
    plugin_id = fields.CharField(max_length=100, description="Plugin identifier")
    enabled = fields.BooleanField(default=True, description="Whether plugin is enabled")
    has_access = fields.BooleanField(default=True, description="Whether org has access (for private plugins)")
    access_granted_at = fields.DatetimeField(null=True, description="When access was granted")
    access_granted_by = fields.ForeignKeyField(
        "models.User",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="granted_plugin_access",
        description="Admin who granted access",
    )
    enabled_at = fields.DatetimeField(null=True, description="When plugin was enabled")
    enabled_by = fields.ForeignKeyField(
        "models.User",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="enabled_plugins",
        description="User who enabled the plugin",
    )
    config = fields.JSONField(null=True, description="Organization-specific config overrides")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "organization_plugins"
        unique_together = (("organization", "plugin_id"),)

    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"OrgPlugin(org={self.organization_id}, plugin={self.plugin_id}, {status})"


class PluginMigration(Model):
    """
    Plugin migration tracking.

    Tracks which migrations have been applied for each plugin,
    separate from core Aerich migrations.
    """

    id = fields.IntField(pk=True)
    plugin_id = fields.CharField(max_length=100, description="Plugin identifier")
    version = fields.CharField(max_length=50, description="Plugin version")
    migration_name = fields.CharField(max_length=255, description="Migration identifier")
    applied_at = fields.DatetimeField(auto_now_add=True, description="When migration was applied")
    success = fields.BooleanField(default=True, description="Whether migration succeeded")
    error_message = fields.TextField(null=True, description="Error message if failed")

    class Meta:
        table = "plugin_migrations"
        unique_together = (("plugin_id", "migration_name"),)

    def __str__(self) -> str:
        status = "success" if self.success else "failed"
        return f"PluginMigration({self.plugin_id}:{self.migration_name}, {status})"
