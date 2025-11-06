"""
Audit log repository for data access.

This module provides data access methods for AuditLog model.
"""

from models import AuditLog, User
from typing import Optional, Any


class AuditRepository:
    """
    Repository for AuditLog data access.

    This class encapsulates all database operations for AuditLog model.
    """

    async def create(
        self,
        user: Optional[User],
        action: str,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        organization_id: Optional[int] = None,
    ) -> AuditLog:
        """
        Create a new audit log entry.

        Args:
            user: User who performed the action
            action: Action name/type
            details: Additional details about the action
            ip_address: IP address of the user

        Returns:
            AuditLog: Created audit log entry
        """
        return await AuditLog.create(
            user=user,
            action=action,
            details=details,
            ip_address=ip_address,
            organization_id=organization_id,
        )

    async def get_recent(self, limit: int = 100) -> list[AuditLog]:
        """
        Get recent audit logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            list[AuditLog]: Recent audit log entries
        """
        return await AuditLog.all().prefetch_related('user').limit(limit)

    async def get_by_user(self, user_id: int, limit: int = 100) -> list[AuditLog]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of logs to return

        Returns:
            list[AuditLog]: User's audit log entries
        """
        return await AuditLog.filter(user_id=user_id).prefetch_related('user').limit(limit)

    async def get_recent_for_org(self, organization_id: int, limit: int = 100) -> list[AuditLog]:
        """
        Get recent audit logs for a specific organization.

        Args:
            organization_id: Organization ID
            limit: Maximum number of logs to return

        Returns:
            list[AuditLog]: Recent audit log entries for the organization
        """
        return await (
            AuditLog.filter(organization_id=organization_id)
            .prefetch_related('user')
            .limit(limit)
        )

    async def get_by_user_in_org(self, user_id: int, organization_id: int, limit: int = 100) -> list[AuditLog]:
        """
        Get audit logs for a user within a specific organization.

        Args:
            user_id: User ID
            organization_id: Organization ID
            limit: Maximum number of logs to return

        Returns:
            list[AuditLog]: User's audit log entries scoped to the organization
        """
        return await (
            AuditLog.filter(user_id=user_id, organization_id=organization_id)
            .prefetch_related('user')
            .limit(limit)
        )

    async def get_by_action(self, action: str, limit: int = 100) -> list[AuditLog]:
        """
        Get audit logs by action type.

        Args:
            action: Action name/type
            limit: Maximum number of logs to return

        Returns:
            list[AuditLog]: Audit log entries for the action
        """
        return await AuditLog.filter(action=action).prefetch_related('user').limit(limit)

    async def list_with_filters(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        organization_id: Optional[int] = None,
    ) -> tuple[list[AuditLog], int]:
        """
        List audit logs with optional filters and pagination.

        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            user_id: Optional user ID filter
            action: Optional action filter
            organization_id: Optional organization ID filter

        Returns:
            Tuple of (logs, total_count)
        """
        query = AuditLog.all()

        if user_id is not None:
            query = query.filter(user_id=user_id)
        if action is not None:
            query = query.filter(action=action)
        if organization_id is not None:
            query = query.filter(organization_id=organization_id)

        total = await query.count()
        logs = await query.prefetch_related('user').order_by('-created_at').offset(offset).limit(limit)

        return logs, total

    async def get_speedgaming_sync_logs_for_tournament(
        self,
        organization_id: int,
        tournament_id: int,
        limit: int = 10
    ) -> list[AuditLog]:
        """
        Get SpeedGaming sync logs for a specific tournament.

        Note: Since details is a JSON field and Tortoise ORM doesn't support
        JSON field queries, we fetch recent sync logs for the organization
        and filter in Python.

        Args:
            organization_id: Organization ID
            tournament_id: Tournament ID
            limit: Maximum number of logs to return

        Returns:
            list[AuditLog]: SpeedGaming sync logs for the tournament
        """
        # Fetch recent sync logs for the organization (fetch more to account for filtering)
        all_sync_logs = await AuditLog.filter(
            action="speedgaming_sync",
            organization_id=organization_id
        ).order_by('-created_at').limit(50).all()

        # Filter for this tournament in Python
        tournament_logs = [
            log for log in all_sync_logs
            if log.details and log.details.get('tournament_id') == tournament_id
        ][:limit]

        return tournament_logs
