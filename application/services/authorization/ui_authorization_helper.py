"""UI Authorization Helper Service.

Provides simplified authorization checks for frontend UI components.
Wraps AuthorizationServiceV2 with UI-friendly method names and return types.
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from models import User
from application.services.authorization.authorization_service_v2 import AuthorizationServiceV2

logger = logging.getLogger(__name__)


@dataclass
class UIPermissions:
    """UI permissions for an organization and user."""
    
    # Tournament Management
    can_manage_tournaments: bool = False
    can_create_tournaments: bool = False
    can_update_tournaments: bool = False
    can_delete_tournaments: bool = False
    can_view_tournaments: bool = False
    
    # Async Tournament Management
    can_manage_async_tournaments: bool = False
    can_review_async_races: bool = False
    
    # Member Management
    can_manage_members: bool = False
    can_invite_members: bool = False
    can_remove_members: bool = False
    can_update_member_permissions: bool = False
    
    # Organization Settings
    can_manage_organization: bool = False
    can_update_organization_settings: bool = False
    can_view_organization_settings: bool = False
    
    # Scheduled Tasks
    can_manage_scheduled_tasks: bool = False
    can_create_scheduled_tasks: bool = False
    can_execute_scheduled_tasks: bool = False
    
    # Race Room Profiles
    can_manage_race_room_profiles: bool = False
    can_create_race_room_profiles: bool = False
    can_update_race_room_profiles: bool = False
    can_delete_race_room_profiles: bool = False
    
    # Live Races
    can_manage_live_races: bool = False
    
    # General
    is_organization_member: bool = False
    is_organization_admin: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return asdict(self)


class UIAuthorizationHelper:
    """Helper service for UI authorization checks."""
    
    def __init__(self):
        self.auth = AuthorizationServiceV2()
    
    async def get_organization_permissions(
        self,
        user: Optional[User],
        organization_id: int
    ) -> UIPermissions:
        """
        Get all permissions for a user in an organization.
        
        Args:
            user: User to check permissions for
            organization_id: Organization ID
            
        Returns:
            UIPermissions object with all permission flags set
        """
        if not user:
            return UIPermissions()
        
        permissions = UIPermissions()
        
        # Check global admin permissions (SUPERADMIN and ADMIN bypass membership requirements)
        from models import Permission
        if user.permission >= Permission.ADMIN:
            # Global admin - grant all permissions
            permissions.is_organization_member = True
            permissions.is_organization_admin = True
            permissions.can_manage_tournaments = True
            permissions.can_create_tournaments = True
            permissions.can_update_tournaments = True
            permissions.can_delete_tournaments = True
            permissions.can_view_tournaments = True
            permissions.can_manage_async_tournaments = True
            permissions.can_review_async_races = True
            permissions.can_manage_members = True
            permissions.can_invite_members = True
            permissions.can_remove_members = True
            permissions.can_update_member_permissions = True
            permissions.can_manage_organization = True
            permissions.can_update_organization_settings = True
            permissions.can_view_organization_settings = True
            permissions.can_manage_scheduled_tasks = True
            permissions.can_create_scheduled_tasks = True
            permissions.can_execute_scheduled_tasks = True
            permissions.can_manage_race_room_profiles = True
            permissions.can_create_race_room_profiles = True
            permissions.can_update_race_room_profiles = True
            permissions.can_delete_race_room_profiles = True
            permissions.can_manage_live_races = True
            return permissions
        
        # Check membership
        permissions.is_organization_member = await self._check_membership(user, organization_id)
        
        if not permissions.is_organization_member:
            # Not a member - no permissions
            return permissions
        
        # Check if organization admin (has all permissions)
        permissions.is_organization_admin = await self._is_organization_admin(user, organization_id)
        
        # Tournament permissions
        permissions.can_manage_tournaments = await self._can_manage_tournaments(user, organization_id)
        permissions.can_create_tournaments = permissions.can_manage_tournaments
        permissions.can_update_tournaments = permissions.can_manage_tournaments
        permissions.can_delete_tournaments = permissions.can_manage_tournaments
        permissions.can_view_tournaments = permissions.is_organization_member  # All members can view
        
        # Async tournament permissions
        permissions.can_manage_async_tournaments = await self._can_manage_async_tournaments(user, organization_id)
        permissions.can_review_async_races = await self._can_review_async_races(user, organization_id)
        
        # Member management permissions
        permissions.can_manage_members = await self._can_manage_members(user, organization_id)
        permissions.can_invite_members = permissions.can_manage_members
        permissions.can_remove_members = permissions.can_manage_members
        permissions.can_update_member_permissions = permissions.can_manage_members
        
        # Organization settings permissions
        permissions.can_manage_organization = await self._can_manage_organization(user, organization_id)
        permissions.can_update_organization_settings = permissions.can_manage_organization
        permissions.can_view_organization_settings = permissions.is_organization_member
        
        # Scheduled tasks permissions
        permissions.can_manage_scheduled_tasks = await self._can_manage_scheduled_tasks(user, organization_id)
        permissions.can_create_scheduled_tasks = permissions.can_manage_scheduled_tasks
        permissions.can_execute_scheduled_tasks = permissions.can_manage_scheduled_tasks
        
        # Race room profiles permissions
        permissions.can_manage_race_room_profiles = await self._can_manage_race_room_profiles(user, organization_id)
        permissions.can_create_race_room_profiles = permissions.can_manage_race_room_profiles
        permissions.can_update_race_room_profiles = permissions.can_manage_race_room_profiles
        permissions.can_delete_race_room_profiles = permissions.can_manage_race_room_profiles
        
        # Live races permissions
        permissions.can_manage_live_races = await self._can_manage_live_races(user, organization_id)
        
        return permissions
    
    async def get_multiple_organization_permissions(
        self,
        user: Optional[User],
        organization_ids: List[int]
    ) -> Dict[int, UIPermissions]:
        """
        Get permissions for multiple organizations at once.
        
        Args:
            user: User to check permissions for
            organization_ids: List of organization IDs
            
        Returns:
            Dictionary mapping organization_id to UIPermissions
        """
        result = {}
        for org_id in organization_ids:
            result[org_id] = await self.get_organization_permissions(user, org_id)
        return result
    
    # Individual permission checks
    
    async def can_manage_tournaments(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can manage tournaments."""
        if not user:
            return False
        return await self._can_manage_tournaments(user, organization_id)
    
    async def can_manage_async_tournaments(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can manage async tournaments."""
        if not user:
            return False
        return await self._can_manage_async_tournaments(user, organization_id)
    
    async def can_review_async_races(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can review async race submissions."""
        if not user:
            return False
        return await self._can_review_async_races(user, organization_id)
    
    async def can_manage_members(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can manage organization members."""
        if not user:
            return False
        return await self._can_manage_members(user, organization_id)
    
    async def can_manage_organization(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can manage organization settings."""
        if not user:
            return False
        return await self._can_manage_organization(user, organization_id)
    
    async def can_manage_scheduled_tasks(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can manage scheduled tasks."""
        if not user:
            return False
        return await self._can_manage_scheduled_tasks(user, organization_id)
    
    async def can_manage_race_room_profiles(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can manage race room profiles."""
        if not user:
            return False
        return await self._can_manage_race_room_profiles(user, organization_id)
    
    async def can_manage_live_races(
        self,
        user: Optional[User],
        organization_id: int
    ) -> bool:
        """Check if user can manage live races."""
        if not user:
            return False
        return await self._can_manage_live_races(user, organization_id)
    
    # Internal helper methods
    
    async def _check_membership(self, user: User, organization_id: int) -> bool:
        """Check if user is a member of the organization."""
        from models import OrganizationMember
        member = await OrganizationMember.get_or_none(
            organization_id=organization_id,
            user_id=user.id
        )
        return member is not None
    
    async def _is_organization_admin(self, user: User, organization_id: int) -> bool:
        """Check if user is an organization admin."""
        # Organization Admin built-in role has all permissions
        return await self.auth.can(
            user,
            action="organization:manage",
            resource=f"organization:{organization_id}",
            organization_id=organization_id
        )
    
    async def _can_manage_tournaments(self, user: User, organization_id: int) -> bool:
        """Internal tournament management check."""
        return await self.auth.can(
            user,
            action="tournament:manage",  # Match service layer action
            resource=self.auth.get_resource_identifier("tournament", "*"),
            organization_id=organization_id
        )
    
    async def _can_manage_async_tournaments(self, user: User, organization_id: int) -> bool:
        """Internal async tournament management check."""
        return await self.auth.can(
            user,
            action="async_tournament:manage",  # Match service layer action
            resource=self.auth.get_resource_identifier("async_tournament", "*"),
            organization_id=organization_id
        )
    
    async def _can_review_async_races(self, user: User, organization_id: int) -> bool:
        """Internal async race review check."""
        return await self.auth.can(
            user,
            action="async_race:review",  # Match service layer action
            resource=self.auth.get_resource_identifier("async_race", "*"),
            organization_id=organization_id
        )
    
    async def _can_manage_members(self, user: User, organization_id: int) -> bool:
        """Internal member management check."""
        return await self.auth.can(
            user,
            action="member:manage",  # Use "member" not "organization_member" to match built-in roles
            resource=self.auth.get_resource_identifier("member", "*"),
            organization_id=organization_id
        )
    
    async def _can_manage_organization(self, user: User, organization_id: int) -> bool:
        """Internal organization management check."""
        return await self.auth.can(
            user,
            action="organization:manage",  # Match service layer action
            resource=self.auth.get_resource_identifier("organization", str(organization_id)),
            organization_id=organization_id
        )
    
    async def _can_manage_scheduled_tasks(self, user: User, organization_id: int) -> bool:
        """Internal scheduled task management check."""
        return await self.auth.can(
            user,
            action="scheduled_task:manage",  # Match service layer action
            resource=self.auth.get_resource_identifier("scheduled_task", "*"),
            organization_id=organization_id
        )
    
    async def _can_manage_race_room_profiles(self, user: User, organization_id: int) -> bool:
        """Internal race room profile management check."""
        return await self.auth.can(
            user,
            action="race_room_profile:manage",  # Match service layer action
            resource=self.auth.get_resource_identifier("race_room_profile", "*"),
            organization_id=organization_id
        )
    
    async def _can_manage_live_races(self, user: User, organization_id: int) -> bool:
        """Internal live race management check."""
        return await self.auth.can(
            user,
            action="async_live_race:manage",  # Match service layer action
            resource=self.auth.get_resource_identifier("async_live_race", "*"),
            organization_id=organization_id
        )
