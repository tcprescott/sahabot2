"""
Organization request repository for data access.

This module provides data access methods for OrganizationRequest model.
"""

from typing import List, Optional
from models.organization_request import OrganizationRequest


class OrganizationRequestRepository:
    """Repository for organization request data access."""

    async def list_pending_requests(self) -> List[OrganizationRequest]:
        """
        List all pending organization requests.

        Returns:
            List of pending requests with related user data
        """
        return await OrganizationRequest.filter(
            status=OrganizationRequest.RequestStatus.PENDING
        ).prefetch_related('requested_by').order_by('-requested_at')

    async def list_reviewed_requests(self) -> List[OrganizationRequest]:
        """
        List all reviewed organization requests (approved or rejected).

        Returns:
            List of reviewed requests with related user data
        """
        return await OrganizationRequest.filter(
            status__in=[
                OrganizationRequest.RequestStatus.APPROVED,
                OrganizationRequest.RequestStatus.REJECTED
            ]
        ).prefetch_related('requested_by', 'reviewed_by').order_by('-reviewed_at')

    async def list_user_pending_requests(self, user_id: int) -> List[OrganizationRequest]:
        """
        List pending requests submitted by a specific user.

        Args:
            user_id: User ID

        Returns:
            List of user's pending requests
        """
        return await OrganizationRequest.filter(
            requested_by_id=user_id,
            status=OrganizationRequest.RequestStatus.PENDING
        ).all()

    async def get_by_id(self, request_id: int) -> Optional[OrganizationRequest]:
        """
        Get an organization request by ID.

        Args:
            request_id: Request ID

        Returns:
            OrganizationRequest if found, None otherwise
        """
        return await OrganizationRequest.get_or_none(id=request_id)
