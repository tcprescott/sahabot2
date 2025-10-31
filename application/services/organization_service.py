"""
Organization service providing business logic for organizations.

This service handles listing, creating, and updating organizations,
permissions CRUD, assigning multiple permissions per member, and
provides helper methods for authorization decisions related to
organization administration.
"""

from typing import Optional, Sequence, Iterable, Dict, List
from models import Organization, User, Permission
from application.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    """Business logic for organizations."""

    def __init__(self) -> None:
        self.repo = OrganizationRepository()

    # Hard-coded permission types available within organizations (name -> description)
    # These define the canonical set of permission names that can be assigned to org members.
    _PERMISSION_TYPES: Dict[str, str] = {
        "ADMIN": "Full administrative access within the organization.",
        "TOURNAMENT_MANAGER": "Create and manage tournaments for the org.",
        "MEMBER_MANAGER": "Add/remove members and set their permissions.",
        "SCHEDULE_MANAGER": "Create and manage schedules or events for the org.",
        "MODERATOR": "Moderate interactions and content for the org.",
    }

    def list_available_permission_types(self) -> List[dict]:
        """Return the list of available organization permission types.

        Each item contains {"name": str, "description": str}.
        """
        return [{"name": name, "description": desc} for name, desc in self._PERMISSION_TYPES.items()]

    def _normalize_name(self, name: str) -> str:
        return (name or "").strip().upper()

    def _validate_permission_names(self, names: Iterable[str]) -> None:
        """Validate that all provided names are in the allowed set.

        Raises:
            ValueError: if any name is not an allowed permission type
        """
        allowed = set(self._PERMISSION_TYPES.keys())
        invalid = [n for n in (self._normalize_name(x) for x in names) if n and n not in allowed]
        if invalid:
            raise ValueError(f"Unknown organization permission(s): {', '.join(sorted(set(invalid)))}")

    async def initialize_default_permissions(self, organization_id: int) -> None:
        """Ensure all default permission definitions exist for an organization."""
        for name in self._PERMISSION_TYPES.keys():
            await self.repo.get_or_create_permission(organization_id, name, self._PERMISSION_TYPES[name])

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

    async def user_can_manage_tournaments(self, user: Optional[User], organization_id: int) -> bool:
        """Check if the user can manage tournaments within the organization.

        Grants if:
        - User can admin the org (global or org-level admin), OR
        - User has the TOURNAMENT_MANAGER org permission
        """
        if await self.user_can_admin_org(user, organization_id):
            return True
        if user is None:
            return False

        # Check org membership and permissions for TOURNAMENT_MANAGER
        member = await self.repo.get_member(organization_id, user.id)
        if not member:
            return False
        await member.fetch_related('permissions')
        permission_names = [p.permission_name for p in getattr(member, 'permissions', [])]
        return 'TOURNAMENT_MANAGER' in permission_names

    # --- Permissions definitions (per-organization) ---

    async def list_permissions(self, organization_id: int):
        """List all permission definitions for an organization.

        Returns a list of OrganizationPermission models.
        """
        return await self.repo.list_permissions(organization_id)

    async def ensure_permissions(self, organization_id: int, names: Iterable[str]) -> None:
        """Ensure the provided permission names exist for the organization.

        Creates any missing OrganizationPermission rows. Does not delete existing.
        """
        self._validate_permission_names(names)
        for name in (self._normalize_name(n) for n in names):
            await self.repo.get_or_create_permission(organization_id, name)

    async def create_permission(self, organization_id: int, permission_name: str, description: Optional[str] = None):
        """Create a permission definition for the organization (idempotent)."""
        normalized = self._normalize_name(permission_name)
        self._validate_permission_names([normalized])
        return await self.repo.get_or_create_permission(organization_id, normalized, description or self._PERMISSION_TYPES.get(normalized))

    async def delete_permission(self, organization_id: int, permission_name: str) -> int:
        """Delete a permission definition by name. Returns number of rows deleted."""
        normalized = self._normalize_name(permission_name)
        self._validate_permission_names([normalized])
        return await self.repo.delete_permission(organization_id, normalized)

    # --- Member permission assignments ---

    async def list_member_permissions(self, organization_id: int, user_id: int) -> list[str]:
        """List permission names assigned to a member within the organization."""
        return await self.repo.list_member_permissions(organization_id, user_id)

    async def add_permissions_to_member(self, organization_id: int, user_id: int, permission_names: Sequence[str]) -> None:
        """Grant one or more permissions to the member (additive)."""
        self._validate_permission_names(permission_names)
        normalized = [self._normalize_name(n) for n in permission_names]
        await self.repo.add_permissions_to_member(organization_id, user_id, normalized)

    async def set_permissions_for_member(self, organization_id: int, user_id: int, permission_names: Sequence[str]) -> None:
        """Replace the member's permissions with the provided list (idempotent)."""
        self._validate_permission_names(permission_names)
        normalized = [self._normalize_name(n) for n in permission_names]
        await self.repo.set_permissions_for_member(organization_id, user_id, normalized)

    async def remove_permissions_from_member(self, organization_id: int, user_id: int, permission_names: Sequence[str]) -> None:
        """Revoke one or more permissions from the member."""
        self._validate_permission_names(permission_names)
        normalized = [self._normalize_name(n) for n in permission_names]
        await self.repo.remove_permissions_from_member(organization_id, user_id, normalized)

    # --- Members management ---

    async def list_members(self, organization_id: int):
        """List all members of an organization with their permissions loaded."""
        return await self.repo.list_members(organization_id)

    async def get_member(self, organization_id: int, user_id: int):
        """Get a specific member with permissions loaded."""
        return await self.repo.get_member(organization_id, user_id)

    async def add_member(self, organization_id: int, user_id: int):
        """Add a user as a member of the organization.

        For now, this immediately adds the member (auto-accept).
        Future: this will create an invite that must be accepted.
        """
        return await self.repo.add_member(organization_id, user_id)

    async def list_user_memberships(self, user_id: int):
        """List all organizations a user is a member of."""
        return await self.repo.list_memberships_for_user(user_id)
