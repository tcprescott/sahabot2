"""
Authorization service for handling permission checks.

This module provides centralized authorization logic separate from business logic.
"""

from models import User, Permission
from typing import Optional


class AuthorizationService:
    """
    Service for handling user authorization and permission checks.
    
    This service centralizes all authorization logic to ensure consistent
    permission checking across the application.
    """
    
    @staticmethod
    def can_access_admin_panel(user: Optional[User]) -> bool:
        """
        Check if user can access the admin panel.
        
        Args:
            user: User to check permissions for
            
        Returns:
            bool: True if user has admin access
        """
        if user is None:
            return False
        return user.has_permission(Permission.ADMIN)
    
    @staticmethod
    def can_moderate(user: Optional[User]) -> bool:
        """
        Check if user can perform moderation actions.
        
        Args:
            user: User to check permissions for
            
        Returns:
            bool: True if user has moderator or higher permissions
        """
        if user is None:
            return False
        return user.has_permission(Permission.MODERATOR)
    
    @staticmethod
    def can_edit_user(user: Optional[User], target_user: User) -> bool:
        """
        Check if user can edit another user's information.
        
        Args:
            user: User attempting the action
            target_user: User being edited
            
        Returns:
            bool: True if user can edit the target user
        """
        if user is None:
            return False
        
        # Users can always edit themselves
        if user.id == target_user.id:
            return True
        
        # Admins can edit users with lower permissions
        if user.has_permission(Permission.ADMIN):
            return user.permission > target_user.permission
        
        return False
    
    @staticmethod
    def can_change_permissions(user: Optional[User], target_user: User, new_permission: Permission) -> bool:
        """
        Check if user can change another user's permissions.
        
        Args:
            user: User attempting the action
            target_user: User whose permissions are being changed
            new_permission: New permission level
            
        Returns:
            bool: True if user can change the permissions
        """
        if user is None:
            return False
        
        # Only superadmins can change permissions
        if not user.has_permission(Permission.SUPERADMIN):
            return False
        
        # Can't change your own permissions
        if user.id == target_user.id:
            return False
        
        # Can't elevate someone to your level or higher
        if new_permission >= user.permission:
            return False
        
        return True
    
    @staticmethod
    def get_accessible_permission_levels(user: Optional[User]) -> list[Permission]:
        """
        Get list of permission levels the user can assign.
        
        Args:
            user: User to check permissions for
            
        Returns:
            list[Permission]: List of assignable permission levels
        """
        if user is None or not user.has_permission(Permission.SUPERADMIN):
            return []
        
        # Superadmins can assign permissions lower than their own
        return [p for p in Permission if p < user.permission]
    
    @staticmethod
    async def can_manage_org_members(user: Optional[User], organization_id: int) -> bool:
        """
        Check if user can manage members in an organization.
        
        Args:
            user: User to check permissions for
            organization_id: Organization to check permissions in
            
        Returns:
            bool: True if user can manage members
        """
        if user is None:
            return False
        
        # SUPERADMINs can manage any organization
        if user.has_permission(Permission.SUPERADMIN):
            return True
        
        # Check if user has ADMIN or MEMBER_MANAGER permission in the org
        from application.repositories.organization_repository import OrganizationRepository
        repo = OrganizationRepository()
        member = await repo.get_member(organization_id, user.id)
        
        if not member:
            return False
        
        # Check if member has any permissions
        await member.fetch_related('permissions')
        permission_names = [p.permission_name for p in member.permissions]
        
        return 'ADMIN' in permission_names or 'MEMBER_MANAGER' in permission_names
