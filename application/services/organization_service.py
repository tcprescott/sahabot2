"""
Organization service providing business logic for organizations.

This service handles listing, creating, and updating organizations,
and provides helper methods for authorization decisions related to
organization administration.
"""

from typing import Optional
from models import Organization, User, Permission
from application.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    """Business logic for organizations."""

    def __init__(self) -> None:
        self.repo = OrganizationRepository()

    async def list_organizations(self) -> list[Organization]:
        """List all organizations."""
        return await self.repo.list_organizations()

    async def get_organization(self, organization_id: int) -> Optional[Organization]:
        """Get an organization by ID."""
        return await self.repo.get_by_id(organization_id)

    async def create_organization(self, name: str, description: Optional[str], is_active: bool = True) -> Organization:
        """Create a new organization.
        
        Note: Caller should ensure the user has global admin privileges.
        """
        return await self.repo.create(name=name, description=description, is_active=is_active)

    async def update_organization(self, organization_id: int, name: str, description: Optional[str], is_active: bool) -> Optional[Organization]:
        """Update an existing organization.
        
        Returns the updated entity or None if not found.
        """
        return await self.repo.update(organization_id=organization_id, name=name, description=description, is_active=is_active)

    async def user_can_admin_org(self, user: Optional[User], organization_id: int) -> bool:
        """Check if the user can administer the given organization.
        
        Rules:
        - SUPERADMIN or ADMIN can access
        - Otherwise, user must be a member with an org-level ADMIN role
        """
        if user is None:
            return False
        if user.has_permission(Permission.ADMIN):
            return True
        return await self.repo.is_user_org_admin(user_id=user.id, organization_id=organization_id)
