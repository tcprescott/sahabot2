"""
Settings models for global and organization-specific configuration.

GlobalSetting: Application-wide configuration key-value pairs
OrganizationSetting: Per-organization configuration overrides
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from .organizations import Organization


class GlobalSetting(Model):
    """
    Global application settings stored as key-value pairs.
    
    Attributes:
        id: Primary key
        key: Unique setting key/identifier
    value: Setting value (stored as string)
        description: Human-readable description of the setting
        is_public: Whether this setting can be read by non-admins
        created_at: When the setting was created
        updated_at: When the setting was last modified
    """
    
    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=255, unique=True, index=True)
    value = fields.TextField()
    description = fields.TextField(null=True)
    is_public = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "global_settings"
        ordering = ["key"]
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.key}: {self.value}"


class OrganizationSetting(Model):
    """
    Organization-specific settings that override or extend global settings.
    
    Attributes:
        id: Primary key
        organization: Foreign key to Organization
        key: Setting key/identifier (unique per organization)
    value: Setting value (stored as string)
        description: Human-readable description
        created_at: When the setting was created
        updated_at: When the setting was last modified
    """
    
    id = fields.IntField(pk=True)
    organization = fields.ForeignKeyField('models.Organization', related_name='settings', index=True)
    key = fields.CharField(max_length=255, index=True)
    value = fields.TextField()
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "organization_settings"
        unique_together = (("organization", "key"),)
        ordering = ["organization", "key"]
    
    def __str__(self) -> str:
        """String representation."""
        org_id = self.organization.id if hasattr(self, 'organization') else 'unknown'
        return f"Org {org_id}.{self.key}: {self.value}"
