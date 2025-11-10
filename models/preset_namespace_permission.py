"""
Preset namespace permission database model.

This module defines the database model for delegating permissions
within preset namespaces.
"""

from tortoise import fields
from tortoise.models import Model


class PresetNamespacePermission(Model):
    """
    Model for preset namespace permissions.

    Allows namespace owners to delegate create, update, and delete
    permissions to other users within their namespace.

    Attributes:
        id: Primary key
        namespace: The preset namespace
        user: The user being granted permissions
        can_create: Whether user can create presets in this namespace
        can_update: Whether user can update presets in this namespace
        can_delete: Whether user can delete presets in this namespace
        created_at: When the permission was granted
        updated_at: When the permission was last modified
    """

    id = fields.IntField(pk=True)
    namespace = fields.ForeignKeyField(
        "models.PresetNamespace",
        related_name="permissions",
        description="Namespace these permissions apply to",
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="namespace_permissions",
        description="User granted these permissions",
    )
    can_create = fields.BooleanField(
        default=False, description="Can create presets in namespace"
    )
    can_update = fields.BooleanField(
        default=False, description="Can update presets in namespace"
    )
    can_delete = fields.BooleanField(
        default=False, description="Can delete presets in namespace"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "preset_namespace_permissions"
        unique_together = (("namespace_id", "user_id"),)
        indexes = (
            ("namespace_id",),
            ("user_id",),
        )

    def __str__(self):
        """Return string representation of permission."""
        perms = []
        if self.can_create:
            perms.append("create")
        if self.can_update:
            perms.append("update")
        if self.can_delete:
            perms.append("delete")
        perm_str = ", ".join(perms) if perms else "none"
        return f"Namespace {self.namespace.id} permissions for user {self.user.id}: {perm_str}"  # type: ignore
