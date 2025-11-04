"""Service layer for Tournament management.

Contains org-scoped business logic and authorization checks.
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import logging

from models import User
from models.match_schedule import Tournament, Match, MatchPlayers, TournamentPlayers
from application.repositories.tournament_repository import TournamentRepository
from application.services.organization_service import OrganizationService
from application.events import (
    EventBus,
    CrewAddedEvent,
    CrewApprovedEvent,
    CrewUnapprovedEvent,
    CrewRemovedEvent,
)

if TYPE_CHECKING:
    from models.match_schedule import Crew

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

    async def create_tournament(self, user: Optional[User], organization_id: int, name: str, description: Optional[str], is_active: bool, tracker_enabled: bool = True) -> Optional[Tournament]:
        """Create a tournament in an org if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized create_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        return await self.repo.create(organization_id, name, description, is_active, tracker_enabled)

    async def update_tournament(self, user: Optional[User], organization_id: int, tournament_id: int, *, name: Optional[str], description: Optional[str], is_active: Optional[bool], tracker_enabled: Optional[bool] = None) -> Optional[Tournament]:
        """Update a tournament if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized update_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        return await self.repo.update(organization_id, tournament_id, name=name, description=description, is_active=is_active, tracker_enabled=tracker_enabled)

    async def delete_tournament(self, user: Optional[User], organization_id: int, tournament_id: int) -> bool:
        """Delete a tournament if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized delete_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return False
        return await self.repo.delete(organization_id, tournament_id)

    async def list_org_matches(self, organization_id: int) -> List[Match]:
        """List all matches for an organization.

        No special authorization - any member can view the event schedule.
        """
        return await self.repo.list_matches_for_org(organization_id)

    async def list_user_matches(self, organization_id: int, user_id: int) -> List[MatchPlayers]:
        """List matches for a specific user in an organization.

        No special authorization - users can view their own matches.
        """
        return await self.repo.list_matches_for_user(organization_id, user_id)

    async def list_user_tournament_registrations(self, organization_id: int, user_id: int) -> List[TournamentPlayers]:
        """List tournament registrations for a user in an organization.

        No special authorization - users can view their own registrations.
        """
        return await self.repo.list_user_tournament_registrations(organization_id, user_id)

    async def list_all_org_tournaments(self, organization_id: int) -> List[Tournament]:
        """List all tournaments in an organization (public listing for members).
        
        No special authorization - any member can view available tournaments.
        """
        return await self.repo.list_all_org_tournaments(organization_id)

    async def register_user_for_tournament(self, organization_id: int, tournament_id: int, user_id: int) -> Optional[TournamentPlayers]:
        """Register a user for a tournament.
        
        Open enrollment - any member can register themselves.
        Returns None if tournament doesn't exist or doesn't belong to the organization.
        """
        return await self.repo.register_user_for_tournament(organization_id, tournament_id, user_id)

    async def admin_register_user_for_tournament(
        self,
        admin_user: Optional[User],
        organization_id: int,
        tournament_id: int,
        user_id: int
    ) -> Optional[TournamentPlayers]:
        """Register a user for a tournament (admin action).
        
        Requires TOURNAMENT_MANAGER permission or org admin privileges.
        Returns None if unauthorized or tournament doesn't exist.
        """
        # Check if admin user has permission to manage tournaments
        can_manage = await self.org_service.user_can_manage_tournaments(admin_user, organization_id)
        if not can_manage:
            logger.warning(
                "Unauthorized admin_register_user_for_tournament by user %s for org %s",
                getattr(admin_user, 'id', None),
                organization_id
            )
            return None

        return await self.repo.register_user_for_tournament(organization_id, tournament_id, user_id)

    async def admin_unregister_user_from_tournament(
        self,
        admin_user: Optional[User],
        organization_id: int,
        tournament_id: int,
        user_id: int
    ) -> bool:
        """Unregister a user from a tournament (admin action).
        
        Requires TOURNAMENT_MANAGER permission or org admin privileges.
        Returns False if unauthorized or user not registered.
        """
        # Check if admin user has permission to manage tournaments
        can_manage = await self.org_service.user_can_manage_tournaments(admin_user, organization_id)
        if not can_manage:
            logger.warning(
                "Unauthorized admin_unregister_user_from_tournament by user %s for org %s",
                getattr(admin_user, 'id', None),
                organization_id
            )
            return False

        return await self.repo.unregister_user_from_tournament(organization_id, tournament_id, user_id)

    async def unregister_user_from_tournament(self, organization_id: int, tournament_id: int, user_id: int) -> bool:
        """Unregister a user from a tournament.
        
        Users can unregister themselves from tournaments.
        """
        return await self.repo.unregister_user_from_tournament(organization_id, tournament_id, user_id)

    async def list_tournament_players(self, organization_id: int, tournament_id: int) -> List[TournamentPlayers]:
        """List all players registered for a tournament.
        
        No special authorization - any member can view tournament registrations.
        """
        return await self.repo.list_tournament_players(organization_id, tournament_id)

    async def create_match(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        player_ids: List[int],
        scheduled_at: Optional[datetime] = None,
        comment: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[Match]:
        """Create a match for a tournament.
        
        Open access - any member can submit a match request.
        In the future, this might require approval from tournament organizers.
        """
        # Verify user is a member of the organization
        if not user:
            logger.warning("Unauthenticated attempt to create match for org %s", organization_id)
            return None

        member = await self.org_service.get_member(organization_id, user.id)
        if not member:
            logger.warning("User %s is not a member of org %s, cannot create match", user.id, organization_id)
            return None

        return await self.repo.create_match(
            organization_id=organization_id,
            tournament_id=tournament_id,
            player_ids=player_ids,
            scheduled_at=scheduled_at,
            comment=comment,
            title=title,
        )

    async def update_match(
        self,
        user: Optional[User],
        organization_id: int,
        match_id: int,
        *,
        title: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        stream_channel_id: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> Optional[Match]:
        """Update a match.
        
        Requires TOURNAMENT_MANAGER permission or MODERATOR permission.
        """
        # Check if user can manage tournaments (tournament admin) or is a moderator
        can_manage = await self.org_service.user_can_manage_tournaments(user, organization_id)
        
        if not can_manage:
            # Check if user is at least a moderator
            from application.services.authorization_service import AuthorizationService
            auth_z = AuthorizationService()
            if not auth_z.can_moderate(user):
                logger.warning("Unauthorized update_match by user %s for org %s", getattr(user, 'id', None), organization_id)
                return None
        
        return await self.repo.update_match(
            organization_id=organization_id,
            match_id=match_id,
            title=title,
            scheduled_at=scheduled_at,
            stream_channel_id=stream_channel_id,
            comment=comment,
        )

    async def signup_crew(self, user: User, organization_id: int, match_id: int, role: str) -> Optional['Crew']:
        """Sign up as crew for a match.
        
        Any member can sign up. Requires approval from tournament manager.
        """
        from models.match_schedule import Crew
        
        # Verify user is a member of the organization
        member = await self.org_service.get_member(organization_id, user.id)
        if not member:
            logger.warning("User %s is not a member of org %s, cannot sign up as crew", user.id, organization_id)
            return None

        crew = await self.repo.signup_crew(match_id, user.id, role)
        
        if crew:
            # Emit crew added event (self-signup, not approved)
            await EventBus.emit(CrewAddedEvent(
                user_id=user.id,
                organization_id=organization_id,
                entity_id=crew.id,
                match_id=match_id,
                crew_user_id=user.id,
                role=role,
                added_by_admin=False,
                auto_approved=False,
            ))
        
        return crew

    async def remove_crew_signup(self, user: User, organization_id: int, match_id: int, role: str) -> bool:
        """Remove crew signup for a match.
        
        Users can remove their own signups.
        """
        from models.match_schedule import Crew
        
        # Verify user is a member of the organization
        member = await self.org_service.get_member(organization_id, user.id)
        if not member:
            logger.warning("User %s is not a member of org %s, cannot remove crew signup", user.id, organization_id)
            return False

        # Get crew info before removing for event
        crew = await Crew.filter(match_id=match_id, user_id=user.id, role=role).first()
        
        success = await self.repo.remove_crew_signup(match_id, user.id, role)
        
        if success and crew:
            # Emit crew removed event
            await EventBus.emit(CrewRemovedEvent(
                user_id=user.id,
                organization_id=organization_id,
                entity_id=crew.id,
                match_id=match_id,
                crew_user_id=user.id,
                role=role,
            ))
        
        return success

    async def admin_add_crew(
        self,
        admin_user: Optional[User],
        organization_id: int,
        match_id: int,
        user_id: int,
        role: str,
        approved: bool = True
    ) -> Optional['Crew']:
        """Add a user as crew for a match (admin action).
        
        Requires ADMIN or TOURNAMENT_MANAGER permission in the organization.
        Admin-added crew is automatically approved by default.
        
        Args:
            admin_user: User performing the admin action
            organization_id: Organization ID for permission check
            match_id: Match ID
            user_id: User ID to add as crew
            role: Crew role (e.g., 'commentator', 'tracker')
            approved: Whether the crew is pre-approved (default True)
        
        Returns:
            The Crew record if successful, None if unauthorized.
        """
        from models.match_schedule import Crew
        
        # Check if admin user has permission to approve crew (same permission level)
        allowed = await self.org_service.user_can_approve_crew(admin_user, organization_id)
        if not allowed:
            logger.warning(
                "Unauthorized admin_add_crew by user %s for org %s",
                getattr(admin_user, 'id', None),
                organization_id
            )
            return None
        
        # Verify the user being added is a member of the organization
        member = await self.org_service.get_member(organization_id, user_id)
        if not member:
            logger.warning(
                "Cannot add user %s as crew - not a member of org %s",
                user_id,
                organization_id
            )
            return None
        
        crew = await self.repo.admin_add_crew(
            match_id=match_id,
            user_id=user_id,
            role=role,
            approved=approved,
            approver_user_id=admin_user.id if approved else None
        )
        
        if crew:
            # Emit crew added event (admin action)
            await EventBus.emit(CrewAddedEvent(
                user_id=admin_user.id,
                organization_id=organization_id,
                entity_id=crew.id,
                match_id=match_id,
                crew_user_id=user_id,
                role=role,
                added_by_admin=True,
                auto_approved=approved,
            ))
        
        return crew

    async def approve_crew(self, user: Optional[User], organization_id: int, crew_id: int) -> Optional['Crew']:
        """Approve a crew signup.
        
        Requires ADMIN, TOURNAMENT_MANAGER, or MODERATOR permission in the organization.
        
        Args:
            user: User attempting to approve the crew
            organization_id: Organization ID for permission check
            crew_id: ID of the crew signup to approve
        
        Returns:
            The approved Crew record or None if unauthorized.
        """
        from models.match_schedule import Crew
        
        # Check permission
        allowed = await self.org_service.user_can_approve_crew(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized crew approval by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        
        # Get crew info before approving
        crew_before = await Crew.filter(id=crew_id).first()
        
        crew = await self.repo.approve_crew(crew_id, user.id)
        
        if crew and crew_before:
            # Emit crew approved event
            await EventBus.emit(CrewApprovedEvent(
                user_id=user.id,
                organization_id=organization_id,
                entity_id=crew_id,
                match_id=crew.match_id,
                crew_user_id=crew.user_id,
                role=crew.role,
                approved_by_user_id=user.id,
            ))
        
        return crew

    async def unapprove_crew(self, user: Optional[User], organization_id: int, crew_id: int) -> Optional['Crew']:
        """Remove approval from a crew signup.
        
        Requires ADMIN, TOURNAMENT_MANAGER, or MODERATOR permission in the organization.
        
        Args:
            user: User attempting to unapprove the crew
            organization_id: Organization ID for permission check
            crew_id: ID of the crew signup to unapprove
        
        Returns:
            The unapproved Crew record or None if unauthorized.
        """
        from models.match_schedule import Crew
        
        # Check permission
        allowed = await self.org_service.user_can_approve_crew(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized crew unapproval by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        
        # Get crew info before unapproving
        crew_before = await Crew.filter(id=crew_id).first()
        
        crew = await self.repo.unapprove_crew(crew_id)
        
        if crew and crew_before:
            # Emit crew unapproved event
            await EventBus.emit(CrewUnapprovedEvent(
                user_id=user.id,
                organization_id=organization_id,
                entity_id=crew_id,
                match_id=crew.match_id,
                crew_user_id=crew.user_id,
                role=crew.role,
            ))
        
        return crew

    async def set_match_seed(self, user: Optional[User], organization_id: int, match_id: int, url: str, description: Optional[str] = None):
        """Set or update seed information for a match.
        
        Requires TOURNAMENT_MANAGER permission.
        Returns the MatchSeed instance or None if unauthorized.
        """
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized set_match_seed by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        
        return await self.repo.create_or_update_match_seed(match_id, url, description)

    async def delete_match_seed(self, user: Optional[User], organization_id: int, match_id: int) -> bool:
        """Delete seed information for a match.
        
        Requires TOURNAMENT_MANAGER permission.
        Returns True if deleted, False if not found or unauthorized.
        """
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized delete_match_seed by user %s for org %s", getattr(user, 'id', None), organization_id)
            return False
        
        return await self.repo.delete_match_seed(match_id)
