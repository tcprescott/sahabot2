"""
Organization repository for data access.

This module provides data access methods for Organization, OrganizationMember,
and OrganizationPermission models.
"""

from typing import Optional
from models import Organization, OrganizationMember


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
