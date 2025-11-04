"""Service layer for OrganizationInvite management.

Contains business logic and authorization checks for invite links.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime
import logging
import re

from models import User
from models.organization_invite import OrganizationInvite
from application.repositories.organization_invite_repository import OrganizationInviteRepository
from application.services.organization_service import OrganizationService
from application.events import EventBus, InviteCreatedEvent, InviteAcceptedEvent

logger = logging.getLogger(__name__)


class OrganizationInviteService:
    """Business logic for organization invite links."""

    def __init__(self) -> None:
        self.repo = OrganizationInviteRepository()
        self.org_service = OrganizationService()

    def validate_slug(self, slug: str) -> tuple[bool, Optional[str]]:
        """Validate an invite slug format.
        
        Returns:
            (is_valid, error_message)
        """
        if not slug:
            return False, "Slug cannot be empty"
        if len(slug) < 3:
            return False, "Slug must be at least 3 characters"
        if len(slug) > 100:
            return False, "Slug must be at most 100 characters"
        if not re.match(r'^[a-zA-Z0-9_-]+$', slug):
            return False, "Slug can only contain letters, numbers, hyphens, and underscores"
        return True, None

    async def list_org_invites(self, user: Optional[User], organization_id: int) -> List[OrganizationInvite]:
        """List invite links for an organization after access check."""
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized list_org_invites by user %s for org %s", getattr(user, 'id', None), organization_id)
            return []
        return await self.repo.list_by_org(organization_id)

    async def create_invite(
        self,
        user: Optional[User],
        organization_id: int,
        slug: str,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> tuple[Optional[OrganizationInvite], Optional[str]]:
        """Create an invite link if user can admin the org.
        
        Returns:
            (invite, error_message)
        """
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized create_invite by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None, "Permission denied"

        # Validate slug
        is_valid, error = self.validate_slug(slug)
        if not is_valid:
            return None, error

        # Check if slug exists
        if await self.repo.slug_exists(slug):
            return None, "This invite link is already in use"

        invite = await self.repo.create(organization_id, slug, user.id, max_uses, expires_at)

        # Emit invite created event
        await EventBus.emit(InviteCreatedEvent(
            user_id=user.id,
            organization_id=organization_id,
            entity_id=invite.id,
            invite_code=slug,
            inviter_user_id=user.id,
        ))

        return invite, None

    async def update_invite(
        self,
        user: Optional[User],
        organization_id: int,
        invite_id: int,
        *,
        is_active: Optional[bool] = None,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> Optional[OrganizationInvite]:
        """Update an invite if user can admin the org."""
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized update_invite by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        return await self.repo.update(organization_id, invite_id, is_active=is_active, max_uses=max_uses, expires_at=expires_at)

    async def delete_invite(self, user: Optional[User], organization_id: int, invite_id: int) -> bool:
        """Delete an invite if user can admin the org."""
        allowed = await self.org_service.user_can_admin_org(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized delete_invite by user %s for org %s", getattr(user, 'id', None), organization_id)
            return False
        return await self.repo.delete(organization_id, invite_id)

    async def get_invite_by_slug(self, slug: str) -> Optional[OrganizationInvite]:
        """Get an invite by slug (public access for join page)."""
        return await self.repo.get_by_slug(slug)

    async def can_use_invite(self, invite: OrganizationInvite) -> tuple[bool, Optional[str]]:
        """Check if an invite can be used.
        
        Returns:
            (can_use, reason_if_not)
        """
        if not invite.is_active:
            return False, "This invite link has been deactivated"
        
        if invite.expires_at and datetime.now() > invite.expires_at:
            return False, "This invite link has expired"
        
        if invite.max_uses is not None and invite.uses_count >= invite.max_uses:
            return False, "This invite link has reached its maximum number of uses"
        
        return True, None

    async def use_invite(self, slug: str, user_id: int) -> tuple[bool, Optional[str]]:
        """Use an invite to join an organization.
        
        Returns:
            (success, error_message)
        """
        invite = await self.repo.get_by_slug(slug)
        if not invite:
            return False, "Invalid invite link"
        
        # Check if invite can be used
        can_use, reason = await self.can_use_invite(invite)
        if not can_use:
            return False, reason
        
        # Check if user is already a member
        existing = await self.org_service.get_member(invite.organization_id, user_id)
        if existing:
            return False, "You are already a member of this organization"
        
        # Add user to organization
        await self.org_service.add_member(invite.organization_id, user_id)

        # Increment uses
        await self.repo.increment_uses(invite.id)

        # Emit invite accepted event
        await EventBus.emit(InviteAcceptedEvent(
            user_id=user_id,
            organization_id=invite.organization_id,
            entity_id=invite.id,
            invite_code=slug,
            accepted_by_user_id=user_id,
        ))

        logger.info("User %s joined org %s via invite %s", user_id, invite.organization_id, invite.id)
        return True, None
