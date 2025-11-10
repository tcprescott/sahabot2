"""
Preset namespace database model.

This module defines the database model for preset namespaces.
Namespaces provide a way to organize presets by user or organization,
allowing multiple presets with the same name in different namespaces.
"""

from tortoise import fields
from tortoise.models import Model


class PresetNamespace(Model):
    """
    Model for preset namespaces.

    Namespaces allow users and organizations to have their own collection
    of presets. Each namespace can be owned by either a user or an organization
    (but not both).

    Attributes:
        id: Primary key
        name: Unique namespace identifier (e.g., username or org slug)
        display_name: Human-friendly display name
        description: Optional description of the namespace
        user: Optional user owner (for personal namespaces)
        organization: Optional organization owner (for org namespaces)
        is_public: Whether the namespace and its presets are publicly visible
        created_at: When the namespace was created
        updated_at: When the namespace was last modified
    """

    id = fields.IntField(pk=True)
    name = fields.CharField(
        100, unique=True, description="Unique namespace identifier (slug)"
    )
    display_name = fields.CharField(200, description="Human-friendly display name")
    description = fields.TextField(
        null=True, description="Optional namespace description"
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="preset_namespaces",
        null=True,
        description="User owner (for personal namespaces)",
    )
    organization = fields.ForeignKeyField(
        "models.Organization",
        related_name="preset_namespaces",
        null=True,
        description="Organization owner (for org namespaces)",
    )
    is_public = fields.BooleanField(
        default=True, description="Whether namespace is publicly visible"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "preset_namespaces"
        indexes = (
            ("user_id",),
            ("organization_id",),
            ("is_public",),
        )

    def __str__(self):
        """Return string representation of namespace."""
        return self.name

    @property
    def owner_type(self) -> str:
        """Return the type of owner (user or organization)."""
        if self.user_id:
            return "user"
        elif self.organization_id:
            return "organization"
        return "none"

    @property
    def is_personal(self) -> bool:
        """Check if this is a personal (user-owned) namespace."""
        return self.user_id is not None

    @property
    def is_organization(self) -> bool:
        """Check if this is an organization-owned namespace."""
        return self.organization_id is not None

    async def can_user_edit(self, user) -> bool:
        """
        Check if a user can edit this namespace.

        Args:
            user: User to check permissions for

        Returns:
            True if user can edit the namespace
        """
        from models import Permission

        # Owner can always edit
        if self.user_id and self.user_id == user.id:
            return True

        # TODO: Check organization permissions when org namespaces are implemented
        # if self.organization_id:
        #     return await check_org_admin(user, self.organization_id)

        # Superadmin can edit anything
        return user.has_permission(Permission.SUPERADMIN)
