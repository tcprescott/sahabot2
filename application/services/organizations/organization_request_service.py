"""
Service layer for OrganizationRequest management.

Contains business logic for handling organization creation requests.
"""

from typing import List, Optional
import logging

from models import User
from models.user import Permission
from models.organization_request import OrganizationRequest
from application.repositories.organization_request_repository import (
    OrganizationRequestRepository,
)

logger = logging.getLogger(__name__)


class OrganizationRequestService:
    """Business logic for organization request handling."""

    def __init__(self) -> None:
        self.repo = OrganizationRequestRepository()

    async def list_pending_requests(
        self, user: Optional[User]
    ) -> List[OrganizationRequest]:
        """
        List pending organization requests.

        Only SUPERADMIN users can view pending requests.

        Args:
            user: Current user

        Returns:
            List of pending requests, or empty list if user is not SUPERADMIN
        """
        if not user or not user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "Unauthorized list_pending_requests by user %s",
                getattr(user, "id", None),
            )
            return []

        return await self.repo.list_pending_requests()

    async def list_reviewed_requests(
        self, user: Optional[User]
    ) -> List[OrganizationRequest]:
        """
        List reviewed organization requests.

        Only SUPERADMIN users can view reviewed requests.

        Args:
            user: Current user

        Returns:
            List of reviewed requests, or empty list if user is not SUPERADMIN
        """
        if not user or not user.has_permission(Permission.SUPERADMIN):
            logger.warning(
                "Unauthorized list_reviewed_requests by user %s",
                getattr(user, "id", None),
            )
            return []

        return await self.repo.list_reviewed_requests()

    async def list_user_pending_requests(self, user: User) -> List[OrganizationRequest]:
        """
        List pending requests submitted by the current user.

        Any authenticated user can view their own pending requests.

        Args:
            user: Current user

        Returns:
            List of user's pending requests
        """
        if not user:
            return []

        return await self.repo.list_user_pending_requests(user.id)
