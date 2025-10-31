"""Repository for Tournament data access.

Enforces organization scoping for all reads and writes.
"""

from __future__ import annotations
from typing import Optional, List
import logging

from models.match_schedule import Tournament

logger = logging.getLogger(__name__)


class TournamentRepository:
    """Data access methods for Tournament model."""

    async def list_by_org(self, organization_id: int) -> List[Tournament]:
        """List tournaments for a specific organization ordered by created date desc."""
        return await Tournament.filter(organization_id=organization_id).order_by('-created_at')

    async def get_for_org(self, organization_id: int, tournament_id: int) -> Optional[Tournament]:
        """Get a tournament by id ensuring it belongs to the organization."""
        return await Tournament.get_or_none(id=tournament_id, organization_id=organization_id)

    async def create(self, organization_id: int, name: str, description: Optional[str] = None, is_active: bool = True) -> Tournament:
        """Create a tournament in the given organization."""
        tournament = await Tournament.create(
            organization_id=organization_id,
            name=name,
            description=description,
            is_active=is_active,
        )
        logger.info("Created tournament %s in org %s", tournament.id, organization_id)
        return tournament

    async def update(self, organization_id: int, tournament_id: int, *, name: Optional[str] = None, description: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[Tournament]:
        """Update a tournament, enforcing org ownership."""
        tournament = await self.get_for_org(organization_id, tournament_id)
        if not tournament:
            return None
        if name is not None:
            tournament.name = name
        if description is not None:
            tournament.description = description
        if is_active is not None:
            tournament.is_active = is_active
        await tournament.save()
        logger.info("Updated tournament %s in org %s", tournament.id, organization_id)
        return tournament

    async def delete(self, organization_id: int, tournament_id: int) -> bool:
        """Delete a tournament within an organization. Returns True if deleted."""
        tournament = await self.get_for_org(organization_id, tournament_id)
        if not tournament:
            return False
        await tournament.delete()
        logger.info("Deleted tournament %s in org %s", tournament_id, organization_id)
        return True
