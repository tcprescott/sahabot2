"""
Organization repository for data access.

This module provides data access methods for Organization, OrganizationMember,
and OrganizationPermission models.
"""

from typing import Optional, Iterable, Sequence
from models import Organization, OrganizationMember, OrganizationPermission


class OrganizationRepository:
    """Repository for organization-related data access."""

    async def list_organizations(self) -> list[Organization]:
        """Return all organizations ordered by name."""
        return await Organization.all().order_by('name')

    async def get_by_id(self, organization_id: int) -> Optional[Organization]:
        """Get an organization by ID."""
        return await Organization.get_or_none(id=organization_id)

    async def create(self, name: str, description: Optional[str] = None, is_active: bool = True) -> Organization:
        """Create a new organization."""
        return await Organization.create(name=name, description=description, is_active=is_active)

    async def update(self, organization_id: int, name: str, description: Optional[str], is_active: bool) -> Optional[Organization]:
        """Update an existing organization. Returns the updated entity or None if not found."""
        org = await Organization.get_or_none(id=organization_id)
        if not org:
            return None
        org.name = name
        org.description = description
        org.is_active = is_active
        await org.save()
        return org

    async def is_user_org_admin(self, user_id: int, organization_id: int) -> bool:
        """Return True if the user has an admin-like membership in the organization.

        Convention: a member is considered org-admin if they have an attached permission
        with `permission_name` equal to "ADMIN". This can be expanded to include other
        elevated roles as needed.
        """
        member = await (
            OrganizationMember
            .filter(user_id=user_id, organization_id=organization_id)
            .prefetch_related('permissions')
            .first()
        )
        if not member:
            return False
        # Check for ADMIN permission on the membership
        for perm in await member.permissions.all():
            if perm.permission_name.upper() == "ADMIN":
                return True
        return False

    # --- Members management ---

    async def list_members(self, organization_id: int) -> list[OrganizationMember]:
        """List all members of an organization with their permissions prefetched."""
        return await (
            OrganizationMember
            .filter(organization_id=organization_id)
            .prefetch_related('user', 'permissions')
            .order_by('joined_at')
        )

    async def count_members(self, organization_id: int) -> int:
        """Count the number of members in an organization."""
        return await OrganizationMember.filter(organization_id=organization_id).count()

    async def get_member(self, organization_id: int, user_id: int) -> Optional[OrganizationMember]:
        """Get a specific member with permissions prefetched."""
        return await (
            OrganizationMember
            .filter(organization_id=organization_id, user_id=user_id)
            .prefetch_related('user', 'permissions')
            .first()
        )

    async def list_memberships_for_user(self, user_id: int) -> list[OrganizationMember]:
        """List all organization memberships for a user with organization prefetched."""
        return await (
            OrganizationMember
            .filter(user_id=user_id)
            .prefetch_related('organization')
            .order_by('joined_at')
        )

    # --- Permissions management ---

    async def list_permissions(self, organization_id: int) -> list[OrganizationPermission]:
        """List all defined permissions for an organization."""
        return await OrganizationPermission.filter(organization_id=organization_id).order_by('permission_name')

    async def get_or_create_permission(self, organization_id: int, permission_name: str, description: Optional[str] = None) -> OrganizationPermission:
        """Get or create a permission definition within an organization."""
        perm = await OrganizationPermission.get_or_none(organization_id=organization_id, permission_name=permission_name)
        if perm:
            # Optionally update description
            if description is not None and perm.description != description:
                perm.description = description
                await perm.save()
            return perm
        return await OrganizationPermission.create(organization_id=organization_id, permission_name=permission_name, description=description)

    async def get_permissions_by_names(self, organization_id: int, names: Iterable[str]) -> list[OrganizationPermission]:
        """Fetch existing OrganizationPermission rows by names."""
        name_list = list(names)
        if not name_list:
            return []
        return await OrganizationPermission.filter(organization_id=organization_id, permission_name__in=name_list)

    async def delete_permission(self, organization_id: int, permission_name: str) -> int:
        """Delete a permission definition by name for an organization."""
        return await OrganizationPermission.filter(organization_id=organization_id, permission_name=permission_name).delete()

    async def _get_or_create_member(self, organization_id: int, user_id: int) -> OrganizationMember:
        member = await OrganizationMember.get_or_none(organization_id=organization_id, user_id=user_id)
        if member:
            return member
        return await OrganizationMember.create(organization_id=organization_id, user_id=user_id)

    async def list_member_permissions(self, organization_id: int, user_id: int) -> list[str]:
        """Return list of permission names assigned to a member within an organization."""
        member = await (
            OrganizationMember
            .filter(organization_id=organization_id, user_id=user_id)
            .prefetch_related('permissions')
            .first()
        )
        if not member:
            return []
        perms = await member.permissions.all()
        return [p.permission_name for p in perms]

    async def add_permissions_to_member(self, organization_id: int, user_id: int, permission_names: Sequence[str]) -> None:
        """Add one or more permissions to a member (no-op for already present)."""
        if not permission_names:
            return
        member = await self._get_or_create_member(organization_id, user_id)
        # Ensure permission rows exist
        perms: list[OrganizationPermission] = []
        for name in permission_names:
            perm = await self.get_or_create_permission(organization_id, name)
            perms.append(perm)
        await member.permissions.add(*perms)

    async def set_permissions_for_member(self, organization_id: int, user_id: int, permission_names: Sequence[str]) -> None:
        """Replace the member's permissions with the provided set (idempotent)."""
        member = await self._get_or_create_member(organization_id, user_id)
        # Ensure target permission rows
        target_perms: list[OrganizationPermission] = []
        for name in permission_names:
            perm = await self.get_or_create_permission(organization_id, name)
            target_perms.append(perm)
        # Load current and compute diffs
        current_perms = await member.permissions.all()
        current_by_name = {p.permission_name: p for p in current_perms}
        target_by_name = {p.permission_name: p for p in target_perms}
        to_add = [p for name, p in target_by_name.items() if name not in current_by_name]
        to_remove = [p for name, p in current_by_name.items() if name not in target_by_name]
        if to_remove:
            await member.permissions.remove(*to_remove)
        if to_add:
            await member.permissions.add(*to_add)

    async def remove_permissions_from_member(self, organization_id: int, user_id: int, permission_names: Sequence[str]) -> None:
        """Remove specified permissions from a member (ignores unknown)."""
        if not permission_names:
            return
        member = await OrganizationMember.get_or_none(organization_id=organization_id, user_id=user_id)
        if not member:
            return
        if not member.permissions:
            return
        perms = await self.get_permissions_by_names(organization_id, permission_names)
        if perms:
            await member.permissions.remove(*perms)

    async def add_member(self, organization_id: int, user_id: int) -> OrganizationMember:
        """Add a user as a member of the organization (idempotent).

        Returns the existing member if already present, otherwise creates a new membership.
        """
        existing = await OrganizationMember.get_or_none(organization_id=organization_id, user_id=user_id)
        if existing:
            return existing
        return await OrganizationMember.create(organization_id=organization_id, user_id=user_id)
