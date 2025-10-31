"""Service layer for Tournament management.

Contains org-scoped business logic and authorization checks.
"""

from __future__ import annotations
from typing import Optional, List
import logging

from models import User
from models.match_schedule import Tournament
from application.repositories.tournament_repository import TournamentRepository
from application.services.organization_service import OrganizationService

logger = logging.getLogger(__name__)


class TournamentService:
    """Business logic for tournaments with organization scoping."""

    def __init__(self) -> None:
        self.repo = TournamentRepository()
        self.org_service = OrganizationService()

    async def list_org_tournaments(self, user: Optional[User], organization_id: int) -> List[Tournament]:
        """List tournaments for an organization after access check."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized list_org_tournaments by user %s for org %s", getattr(user, 'id', None), organization_id)
            return []
        return await self.repo.list_by_org(organization_id)

    async def create_tournament(self, user: Optional[User], organization_id: int, name: str, description: Optional[str], is_active: bool) -> Optional[Tournament]:
        """Create a tournament in an org if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized create_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        return await self.repo.create(organization_id, name, description, is_active)

    async def update_tournament(self, user: Optional[User], organization_id: int, tournament_id: int, *, name: Optional[str], description: Optional[str], is_active: Optional[bool]) -> Optional[Tournament]:
        """Update a tournament if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized update_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        return await self.repo.update(organization_id, tournament_id, name=name, description=description, is_active=is_active)

    async def delete_tournament(self, user: Optional[User], organization_id: int, tournament_id: int) -> bool:
        """Delete a tournament if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized delete_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return False
        return await self.repo.delete(organization_id, tournament_id)
