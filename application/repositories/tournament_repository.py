"""Repository for Tournament data access.

Enforces organization scoping for all reads and writes.
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import logging

from models.match_schedule import Tournament, Match, MatchPlayers, TournamentPlayers

if TYPE_CHECKING:
    from models.match_schedule import Crew

logger = logging.getLogger(__name__)


class TournamentRepository:
    """Data access methods for Tournament model."""

    async def list_by_org(self, organization_id: int) -> List[Tournament]:
        """List tournaments for a specific organization ordered by created date desc."""
        return await Tournament.filter(organization_id=organization_id).order_by('-created_at')

    async def get_for_org(self, organization_id: int, tournament_id: int) -> Optional[Tournament]:
        """Get a tournament by id ensuring it belongs to the organization."""
        return await Tournament.get_or_none(id=tournament_id, organization_id=organization_id)

    async def create(self, organization_id: int, name: str, description: Optional[str] = None, is_active: bool = True, tracker_enabled: bool = True) -> Tournament:
        """Create a tournament in the given organization."""
        tournament = await Tournament.create(
            organization_id=organization_id,
            name=name,
            description=description,
            is_active=is_active,
            tracker_enabled=tracker_enabled,
        )
        logger.info("Created tournament %s in org %s", tournament.id, organization_id)
        return tournament

    async def update(self, organization_id: int, tournament_id: int, *, name: Optional[str] = None, description: Optional[str] = None, is_active: Optional[bool] = None, tracker_enabled: Optional[bool] = None) -> Optional[Tournament]:
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
        if tracker_enabled is not None:
            tournament.tracker_enabled = tracker_enabled
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
        ).prefetch_related('tournament', 'stream_channel', 'crew_members__user', 'seed', 'players__user').order_by('scheduled_at')

    async def list_matches_for_user(self, organization_id: int, user_id: int) -> List[MatchPlayers]:
        """List all matches a user is participating in for an organization."""
        return await MatchPlayers.filter(
            user_id=user_id,
            match__tournament__organization_id=organization_id
        ).prefetch_related('match__tournament', 'match__stream_channel', 'match__players__user').order_by('-match__scheduled_at')

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

    async def list_tournament_players(self, organization_id: int, tournament_id: int) -> List[TournamentPlayers]:
        """List all players registered for a tournament.
        
        Returns empty list if tournament doesn't belong to organization.
        """
        # Verify tournament belongs to organization
        tournament = await self.get_for_org(organization_id, tournament_id)
        if not tournament:
            logger.warning("Cannot list players for tournament %s - tournament not found in org %s", tournament_id, organization_id)
            return []

        return await TournamentPlayers.filter(tournament_id=tournament_id).prefetch_related('user')

    async def create_match(
        self,
        organization_id: int,
        tournament_id: int,
        player_ids: List[int],
        scheduled_at: Optional[datetime] = None,
        comment: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[Match]:
        """Create a match for a tournament with players.
        
        Returns None if tournament doesn't belong to organization.
        """

        # Verify tournament belongs to organization
        tournament = await self.get_for_org(organization_id, tournament_id)
        if not tournament:
            logger.warning("Cannot create match for tournament %s - tournament not found in org %s", tournament_id, organization_id)
            return None

        # Create the match
        match = await Match.create(
            tournament_id=tournament_id,
            scheduled_at=scheduled_at,
            comment=comment,
            title=title,
        )

        # Add players to the match
        for player_id in player_ids:
            await MatchPlayers.create(
                match_id=match.id,
                user_id=player_id,
            )

        logger.info("Created match %s for tournament %s in org %s with %d players", match.id, tournament_id, organization_id, len(player_ids))
        return match

    async def update_match(
        self,
        organization_id: int,
        match_id: int,
        *,
        title: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        stream_channel_id: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> Optional[Match]:
        """Update a match, ensuring it belongs to the organization.
        
        Returns None if match doesn't belong to organization's tournament.
        Returns the updated match otherwise.
        """
        # Get the match and verify it belongs to a tournament in this org
        match = await Match.filter(
            id=match_id,
            tournament__organization_id=organization_id
        ).first()
        
        if not match:
            logger.warning("Cannot update match %s - not found in org %s", match_id, organization_id)
            return None
        
        # Update fields if provided
        if title is not None:
            match.title = title
        if scheduled_at is not None:
            match.scheduled_at = scheduled_at
        if stream_channel_id is not None:
            match.stream_channel_id = stream_channel_id
        if comment is not None:
            match.comment = comment
        
        await match.save()
        logger.info("Updated match %s in org %s", match_id, organization_id)
        return match

    async def signup_crew(self, match_id: int, user_id: int, role: str) -> Optional['Crew']:
        """Sign up a user as crew for a match.
        
        Returns the Crew record if successful, None if already signed up.
        """
        from models.match_schedule import Crew
        
        # Check if already signed up for this role
        existing = await Crew.filter(match_id=match_id, user_id=user_id, role=role).first()
        if existing:
            logger.info("User %s already signed up as %s for match %s", user_id, role, match_id)
            return existing
        
        # Create crew signup
        crew = await Crew.create(
            match_id=match_id,
            user_id=user_id,
            role=role,
            approved=False
        )
        logger.info("User %s signed up as %s for match %s", user_id, role, match_id)
        return crew

    async def admin_add_crew(
        self,
        match_id: int,
        user_id: int,
        role: str,
        approved: bool = True,
        approver_user_id: Optional[int] = None
    ) -> Optional['Crew']:
        """Add a user as crew for a match (admin action).
        
        Admin-added crew is automatically approved by default.
        
        Args:
            match_id: Match ID
            user_id: User ID to add as crew
            role: Crew role (e.g., 'commentator', 'tracker')
            approved: Whether the crew is pre-approved (default True)
            approver_user_id: ID of the admin who added the crew
        
        Returns:
            The Crew record if successful, None if already signed up.
        """
        from models.match_schedule import Crew
        
        # Check if already signed up for this role
        existing = await Crew.filter(match_id=match_id, user_id=user_id, role=role).first()
        if existing:
            logger.info("User %s already signed up as %s for match %s", user_id, role, match_id)
            return existing
        
        # Create crew signup with approval
        crew = await Crew.create(
            match_id=match_id,
            user_id=user_id,
            role=role,
            approved=approved,
            approved_by_id=approver_user_id if approved else None
        )
        logger.info("Admin added user %s as %s for match %s (approved=%s)", user_id, role, match_id, approved)
        return crew

    async def remove_crew_signup(self, match_id: int, user_id: int, role: str) -> bool:
        """Remove a user's crew signup for a match.
        
        Returns True if removed, False if not found.
        """
        from models.match_schedule import Crew
        
        crew = await Crew.filter(match_id=match_id, user_id=user_id, role=role).first()
        if not crew:
            logger.warning("No crew signup found for user %s as %s for match %s", user_id, role, match_id)
            return False
        
        await crew.delete()
        logger.info("Removed crew signup for user %s as %s for match %s", user_id, role, match_id)
        return True

    async def approve_crew(self, crew_id: int, approver_user_id: int) -> Optional['Crew']:
        """Approve a crew signup.
        
        Args:
            crew_id: ID of the crew signup to approve
            approver_user_id: ID of the user approving the crew
        
        Returns:
            The updated Crew record if successful, None if not found.
        """
        from models.match_schedule import Crew
        
        crew = await Crew.filter(id=crew_id).first()
        if not crew:
            logger.warning("No crew signup found with id %s", crew_id)
            return None
        
        crew.approved = True
        crew.approved_by_id = approver_user_id
        await crew.save()
        logger.info("Crew %s approved by user %s", crew_id, approver_user_id)
        return crew

    async def unapprove_crew(self, crew_id: int) -> Optional['Crew']:
        """Remove approval from a crew signup.
        
        Args:
            crew_id: ID of the crew signup to unapprove
        
        Returns:
            The updated Crew record if successful, None if not found.
        """
        from models.match_schedule import Crew
        
        crew = await Crew.filter(id=crew_id).first()
        if not crew:
            logger.warning("No crew signup found with id %s", crew_id)
            return None
        
        crew.approved = False
        crew.approved_by_id = None
        await crew.save()
        logger.info("Crew %s approval removed", crew_id)
        return crew

    async def create_or_update_match_seed(self, match_id: int, url: str, description: Optional[str] = None):
        """Create or update seed information for a match.
        
        Returns the MatchSeed instance.
        """
        from models.match_schedule import MatchSeed
        
        # Try to get existing seed
        seed = await MatchSeed.filter(match_id=match_id).first()
        
        if seed:
            # Update existing
            seed.url = url
            seed.description = description
            await seed.save()
            logger.info("Updated seed for match %s", match_id)
        else:
            # Create new
            seed = await MatchSeed.create(
                match_id=match_id,
                url=url,
                description=description
            )
            logger.info("Created seed for match %s", match_id)
        
        return seed

    async def delete_match_seed(self, match_id: int) -> bool:
        """Delete seed information for a match.
        
        Returns True if deleted, False if not found.
        """
        from models.match_schedule import MatchSeed
        
        seed = await MatchSeed.filter(match_id=match_id).first()
        if not seed:
            logger.warning("No seed found for match %s", match_id)
            return False
        
        await seed.delete()
        logger.info("Deleted seed for match %s", match_id)
        return True
