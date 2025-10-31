"""Repository for Tournament data access.

Enforces organization scoping for all reads and writes.
"""

from __future__ import annotations
from typing import Optional, List
import logging

from models.match_schedule import Tournament, Match, MatchPlayers, TournamentPlayers

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

    async def list_matches_for_org(self, organization_id: int) -> List[Match]:
        """List all matches for tournaments in an organization, ordered by scheduled date."""
        return await Match.filter(
            tournament__organization_id=organization_id
        ).prefetch_related('tournament', 'stream_channel').order_by('scheduled_at')

    async def list_matches_for_user(self, organization_id: int, user_id: int) -> List[MatchPlayers]:
        """List all matches a user is participating in for an organization."""
        return await MatchPlayers.filter(
            user_id=user_id,
            match__tournament__organization_id=organization_id
        ).prefetch_related('match__tournament', 'match__stream_channel').order_by('-match__scheduled_at')

    async def list_user_tournament_registrations(self, organization_id: int, user_id: int) -> List[TournamentPlayers]:
        """List tournaments a user is registered for in an organization."""
        return await TournamentPlayers.filter(
            user_id=user_id,
            tournament__organization_id=organization_id
        ).prefetch_related('tournament')

    async def register_user_for_tournament(self, organization_id: int, tournament_id: int, user_id: int) -> Optional[TournamentPlayers]:
        """Register a user for a tournament.
        
        Returns None if tournament doesn't exist or doesn't belong to the organization.
        Returns the registration if successful (or if already registered).
        """
        # Verify tournament belongs to organization
        tournament = await self.get_for_org(organization_id, tournament_id)
        if not tournament:
            logger.warning("Cannot register user %s for tournament %s - tournament not found in org %s", user_id, tournament_id, organization_id)
            return None
        
        # Check if already registered
        existing = await TournamentPlayers.filter(tournament_id=tournament_id, user_id=user_id).first()
        if existing:
            logger.info("User %s already registered for tournament %s", user_id, tournament_id)
            return existing
        
        # Create registration
        registration = await TournamentPlayers.create(tournament_id=tournament_id, user_id=user_id)
        logger.info("Registered user %s for tournament %s in org %s", user_id, tournament_id, organization_id)
        return registration

    async def unregister_user_from_tournament(self, organization_id: int, tournament_id: int, user_id: int) -> bool:
        """Unregister a user from a tournament.
        
        Returns True if unregistered successfully, False otherwise.
        """
        # Verify tournament belongs to organization
        tournament = await self.get_for_org(organization_id, tournament_id)
        if not tournament:
            logger.warning("Cannot unregister user %s from tournament %s - tournament not found in org %s", user_id, tournament_id, organization_id)
            return False
        
        # Find and delete registration
        registration = await TournamentPlayers.filter(tournament_id=tournament_id, user_id=user_id).first()
        if not registration:
            logger.warning("User %s not registered for tournament %s", user_id, tournament_id)
            return False
        
        await registration.delete()
        logger.info("Unregistered user %s from tournament %s in org %s", user_id, tournament_id, organization_id)
        return True

    async def list_all_org_tournaments(self, organization_id: int) -> List[Tournament]:
        """List all tournaments in an organization (including inactive).
        
        No authorization check - used for public listing to members.
        """
        return await Tournament.filter(organization_id=organization_id).order_by('-created_at')
