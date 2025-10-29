"""
Audit logging service.

This module provides centralized audit logging for tracking user actions.
"""

from models import User, AuditLog
from typing import Optional, Any
from application.repositories.audit_repository import AuditRepository


class AuditService:
    """
    Service for handling audit logging.
    
    This service provides methods to log user actions for security and compliance.
    """
    
    def __init__(self):
        """Initialize the audit service with required repositories."""
        self.audit_repository = AuditRepository()
    
    async def log_action(
        self,
        user: Optional[User],
        action: str,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Log a user action.
        
        Args:
            user: User who performed the action (None for system actions)
            action: Action name/type
            details: Additional details about the action
            ip_address: IP address of the user
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await self.audit_repository.create(
            user=user,
            action=action,
            details=details,
            ip_address=ip_address
        )
    
    async def log_login(self, user: User, ip_address: Optional[str] = None) -> AuditLog:
        """
        Log a user login.
        
        Args:
            user: User who logged in
            ip_address: IP address of the user
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await self.log_action(
            user=user,
            action="user_login",
            details={"discord_id": user.discord_id},
            ip_address=ip_address
        )
    
    async def log_permission_change(
        self,
        admin_user: User,
        target_user: User,
        old_permission: int,
        new_permission: int,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Log a permission change.
        
        Args:
            admin_user: User who made the change
            target_user: User whose permissions were changed
            old_permission: Previous permission level
            new_permission: New permission level
            ip_address: IP address of the admin user
            
        Returns:
            AuditLog: Created audit log entry
        """
        return await self.log_action(
            user=admin_user,
            action="permission_change",
            details={
                "target_user_id": target_user.id,
                "target_username": target_user.discord_username,
                "old_permission": old_permission,
                "new_permission": new_permission
            },
            ip_address=ip_address
        )
    
    async def get_recent_logs(self, limit: int = 100) -> list[AuditLog]:
        """
        Get recent audit logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            list[AuditLog]: Recent audit log entries
        """
        return await self.audit_repository.get_recent(limit=limit)
    
    async def get_user_logs(self, user_id: int, limit: int = 100) -> list[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of logs to return
            
        Returns:
            list[AuditLog]: User's audit log entries
        """
        return await self.audit_repository.get_by_user(user_id=user_id, limit=limit)
