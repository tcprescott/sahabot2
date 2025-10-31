

"""Service layer for StreamChannel management.

Contains org-scoped business logic and authorization checks.
"""

from __future__ import annotations
from typing import Optional, List
import logging

from models import User
from models.match_schedule import StreamChannel
from application.repositories.stream_channel_repository import StreamChannelRepository
from application.services.organization_service import OrganizationService

logger = logging.getLogger(__name__)


class StreamChannelService:
    """Business logic for stream channels with organization scoping."""

    def __init__(self) -> None:
        self.repo = StreamChannelRepository()
        self.org_service = OrganizationService()

    async def list_org_channels(self, user: Optional[User], organization_id: int) -> List[StreamChannel]:
        """List stream channels for an organization after access check."""
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized list_org_channels by user %s for org %s", getattr(user, 'id', None), organization_id)
            return []
        return await self.repo.list_by_org(organization_id)

    async def create_channel(self, user: Optional[User], organization_id: int, name: str, stream_url: Optional[str], is_active: bool) -> Optional[StreamChannel]:
        """Create a stream channel in an org if user can admin the org."""
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized create_channel by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        return await self.repo.create(organization_id, name, stream_url, is_active)

    async def update_channel(self, user: Optional[User], organization_id: int, channel_id: int, *, name: Optional[str], stream_url: Optional[str], is_active: Optional[bool]) -> Optional[StreamChannel]:
        """Update a stream channel if user can admin the org."""
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized update_channel by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        return await self.repo.update(organization_id, channel_id, name=name, stream_url=stream_url, is_active=is_active)

    async def delete_channel(self, user: Optional[User], organization_id: int, channel_id: int) -> bool:
        """Delete a stream channel if user can admin the org."""
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized delete_channel by user %s for org %s", getattr(user, 'id', None), organization_id)
            return False
        return await self.repo.delete(organization_id, channel_id)
