"""Repository for OrganizationInvite data access.

Enforces organization scoping for all reads and writes.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime
import logging

from models.organization_invite import OrganizationInvite

logger = logging.getLogger(__name__)


class OrganizationInviteRepository:
    """Data access methods for OrganizationInvite model."""

    async def list_by_org(self, organization_id: int) -> List[OrganizationInvite]:
        """List all invite links for a specific organization."""
        return await OrganizationInvite.filter(
            organization_id=organization_id
        ).order_by("-created_at")

    async def get_by_slug(self, slug: str) -> Optional[OrganizationInvite]:
        """Get an invite by its slug."""
        return await OrganizationInvite.get_or_none(slug=slug)

    async def get_for_org(
        self, organization_id: int, invite_id: int
    ) -> Optional[OrganizationInvite]:
        """Get an invite by id ensuring it belongs to the organization."""
        return await OrganizationInvite.get_or_none(
            id=invite_id, organization_id=organization_id
        )

    async def create(
        self,
        organization_id: int,
        slug: str,
        created_by_id: int,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> OrganizationInvite:
        """Create an invite link."""
        invite = await OrganizationInvite.create(
            organization_id=organization_id,
            slug=slug,
            created_by_id=created_by_id,
            max_uses=max_uses,
            expires_at=expires_at,
            is_active=True,
        )
        logger.info("Created invite %s for org %s", invite.id, organization_id)
        return invite

    async def update(
        self,
        organization_id: int,
        invite_id: int,
        *,
        is_active: Optional[bool] = None,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> Optional[OrganizationInvite]:
        """Update an invite, enforcing org ownership."""
        invite = await self.get_for_org(organization_id, invite_id)
        if not invite:
            return None
        if is_active is not None:
            invite.is_active = is_active
        if max_uses is not None:
            invite.max_uses = max_uses
        if expires_at is not None:
            invite.expires_at = expires_at
        await invite.save()
        logger.info("Updated invite %s in org %s", invite.id, organization_id)
        return invite

    async def increment_uses(self, invite_id: int) -> None:
        """Increment the uses count for an invite."""
        invite = await OrganizationInvite.get_or_none(id=invite_id)
        if invite:
            invite.uses_count += 1
            await invite.save()
            logger.info(
                "Incremented uses for invite %s (now %s)", invite_id, invite.uses_count
            )

    async def delete(self, organization_id: int, invite_id: int) -> bool:
        """Delete an invite within an organization. Returns True if deleted."""
        invite = await self.get_for_org(organization_id, invite_id)
        if not invite:
            return False
        await invite.delete()
        logger.info("Deleted invite %s in org %s", invite_id, organization_id)
        return True

    async def slug_exists(self, slug: str) -> bool:
        """Check if a slug is already in use."""
        return await OrganizationInvite.filter(slug=slug).exists()
