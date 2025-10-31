"""Repository for StreamChannel data access.

Enforces organization scoping for all reads and writes.
"""

from __future__ import annotations
from typing import Optional, List
import logging

from models.match_schedule import StreamChannel

logger = logging.getLogger(__name__)


class StreamChannelRepository:
    """Data access methods for StreamChannel model."""

    async def list_by_org(self, organization_id: int) -> List[StreamChannel]:
        """List stream channels for a specific organization ordered by name."""
        return await StreamChannel.filter(organization_id=organization_id).order_by('name')

    async def get_for_org(self, organization_id: int, channel_id: int) -> Optional[StreamChannel]:
        """Get a stream channel by id ensuring it belongs to the organization."""
        return await StreamChannel.get_or_none(id=channel_id, organization_id=organization_id)

    async def create(self, organization_id: int, name: str, stream_url: Optional[str] = None, is_active: bool = True) -> StreamChannel:
        """Create a stream channel in the given organization."""
        channel = await StreamChannel.create(
            organization_id=organization_id,
            name=name,
            stream_url=stream_url,
            is_active=is_active,
        )
        logger.info("Created stream channel %s in org %s", channel.id, organization_id)
        return channel

    async def update(self, organization_id: int, channel_id: int, *, name: Optional[str] = None, stream_url: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[StreamChannel]:
        """Update a stream channel, enforcing org ownership."""
        channel = await self.get_for_org(organization_id, channel_id)
        if not channel:
            return None
        if name is not None:
            channel.name = name
        if stream_url is not None:
            channel.stream_url = stream_url
        if is_active is not None:
            channel.is_active = is_active
        await channel.save()
        logger.info("Updated stream channel %s in org %s", channel.id, organization_id)
        return channel

    async def delete(self, organization_id: int, channel_id: int) -> bool:
        """Delete a stream channel within an organization. Returns True if deleted."""
        channel = await self.get_for_org(organization_id, channel_id)
        if not channel:
            return False
        await channel.delete()
        logger.info("Deleted stream channel %s in org %s", channel_id, organization_id)
        return True
