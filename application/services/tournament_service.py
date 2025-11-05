"""Service layer for Tournament management.

Contains org-scoped business logic and authorization checks.
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import logging

from models import User, SYSTEM_USER_ID
from models.match_schedule import Tournament, Match, MatchPlayers, TournamentPlayers
from application.repositories.tournament_repository import TournamentRepository
from application.services.organization_service import OrganizationService
from application.events import (
    EventBus,
    CrewAddedEvent,
    CrewApprovedEvent,
    CrewUnapprovedEvent,
    CrewRemovedEvent,
    MatchChannelAssignedEvent,
    MatchChannelUnassignedEvent,
    MatchScheduledEvent,
    MatchFinishedEvent,
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

    async def list_active_org_tournaments(self, user: Optional[User], organization_id: int) -> List[Tournament]:
        """
        List active tournaments for an organization.

        This method is accessible to all organization members (no special permission check).
        Used for displaying active tournaments in the UI.

        Args:
            user: Current user (must be a member of the organization)
            organization_id: Organization ID

        Returns:
            List of active tournaments, or empty list if user is not a member
        """
        # Check if user is a member of the organization
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning("Non-member user %s attempted to list active tournaments for org %s", getattr(user, 'id', None), organization_id)
            return []
        return await self.repo.list_active_by_org(organization_id)

    async def get_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int
    ) -> Optional[Tournament]:
        """
        Get a tournament by ID for an organization.

        Accessible to all organization members.

        Args:
            user: Current user (must be a member of the organization)
            organization_id: Organization ID
            tournament_id: Tournament ID

        Returns:
            Tournament if found and user is a member, None otherwise
        """
        # Check if user is a member of the organization
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning("Non-member user %s attempted to get tournament %s for org %s", getattr(user, 'id', None), tournament_id, organization_id)
            return None
        return await self.repo.get_for_org(organization_id, tournament_id)

    async def create_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        name: str,
        description: Optional[str],
        is_active: bool,
        tracker_enabled: bool = True,
        racetime_bot_id: Optional[int] = None,
        racetime_auto_create: bool = False,
        room_open_minutes: int = 60,
        require_racetime_link: bool = False,
        racetime_default_goal: Optional[str] = None,
        create_scheduled_events: bool = False,
        scheduled_events_enabled: bool = True,
        discord_guild_ids: Optional[list[int]] = None,
    ) -> Optional[Tournament]:
        """Create a tournament in an org if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized create_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None
        
        tournament = await self.repo.create(
            organization_id,
            name,
            description,
            is_active,
            tracker_enabled,
            racetime_bot_id=racetime_bot_id,
            racetime_auto_create_rooms=racetime_auto_create,
            room_open_minutes_before=room_open_minutes,
            require_racetime_link=require_racetime_link,
            racetime_default_goal=racetime_default_goal,
            create_scheduled_events=create_scheduled_events,
            scheduled_events_enabled=scheduled_events_enabled,
        )
        
        # Set discord guilds if provided
        if tournament and discord_guild_ids:
            from models import DiscordGuild
            guilds = await DiscordGuild.filter(id__in=discord_guild_ids, organization_id=organization_id).all()
            await tournament.discord_event_guilds.add(*guilds)
        
        return tournament

    async def update_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        tracker_enabled: Optional[bool] = None,
        racetime_bot_id: Optional[int] = None,
        racetime_auto_create: Optional[bool] = None,
        room_open_minutes: Optional[int] = None,
        require_racetime_link: Optional[bool] = None,
        racetime_default_goal: Optional[str] = None,
        race_room_profile_id: Optional[int] = None,
        create_scheduled_events: Optional[bool] = None,
        scheduled_events_enabled: Optional[bool] = None,
        discord_guild_ids: Optional[list[int]] = None,
        discord_event_filter: Optional[str] = None,
        event_duration_minutes: Optional[int] = None,
    ) -> Optional[Tournament]:
        """Update a tournament if user can admin the org."""
        allowed = await self.org_service.user_can_manage_tournaments(user, organization_id)
        if not allowed:
            logger.warning("Unauthorized update_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None

        # Build update kwargs
        updates = {}
        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if is_active is not None:
            updates['is_active'] = is_active
        if tracker_enabled is not None:
            updates['tracker_enabled'] = tracker_enabled
        if racetime_bot_id is not None:
            updates['racetime_bot_id'] = racetime_bot_id
        if racetime_auto_create is not None:
            updates['racetime_auto_create_rooms'] = racetime_auto_create
        if room_open_minutes is not None:
            updates['room_open_minutes_before'] = room_open_minutes
        if require_racetime_link is not None:
            updates['require_racetime_link'] = require_racetime_link
        if racetime_default_goal is not None:
            updates['racetime_default_goal'] = racetime_default_goal
        if race_room_profile_id is not None:
            updates['race_room_profile_id'] = race_room_profile_id
        if create_scheduled_events is not None:
            updates['create_scheduled_events'] = create_scheduled_events
        if scheduled_events_enabled is not None:
            updates['scheduled_events_enabled'] = scheduled_events_enabled
        if discord_event_filter is not None:
            updates['discord_event_filter'] = discord_event_filter
        if event_duration_minutes is not None:
            updates['event_duration_minutes'] = event_duration_minutes

        tournament = await self.repo.update(organization_id, tournament_id, **updates)
        
        # Update discord guilds if provided
        if tournament and discord_guild_ids is not None:
            from models import DiscordGuild
            # Clear existing guilds
            await tournament.discord_event_guilds.clear()
            # Add new guilds
            if discord_guild_ids:
                guilds = await DiscordGuild.filter(id__in=discord_guild_ids, organization_id=organization_id).all()
                await tournament.discord_event_guilds.add(*guilds)
        
        return tournament

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
        
        Raises:
            ValueError: If tournament requires RaceTime link and players don't have it
        """
        # Verify user is a member of the organization
        if not user:
            logger.warning("Unauthenticated attempt to create match for org %s", organization_id)
            return None

        member = await self.org_service.get_member(organization_id, user.id)
        if not member:
            logger.warning("User %s is not a member of org %s, cannot create match", user.id, organization_id)
            return None

        # Validate RaceTime requirements if tournament has them enabled
        tournament = await self.repo.get_for_org(organization_id, tournament_id)
        if tournament and tournament.require_racetime_link:
            # Check that all players have RaceTime accounts linked
            from models.user import User as UserModel
            players = await UserModel.filter(id__in=player_ids).all()
            
            players_without_racetime = [
                p.discord_username for p in players if not p.racetime_id
            ]
            
            if players_without_racetime:
                player_list = ", ".join(players_without_racetime)
                error_msg = f"This tournament requires RaceTime accounts. The following players must link their accounts first: {player_list}"
                logger.warning(
                    "Match creation blocked - players without RaceTime: %s (tournament %s)",
                    player_list,
                    tournament_id
                )
                raise ValueError(error_msg)

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
        
        # Get the match before update to check channel changes and schedule changes
        match_before = await Match.filter(
            id=match_id,
            tournament__organization_id=organization_id
        ).select_related('stream_channel', 'tournament').prefetch_related('players__user').first()

        if not match_before:
            logger.warning("Match %s not found in org %s", match_id, organization_id)
            return None

        previous_channel_id = match_before.stream_channel_id
        previous_scheduled_at = match_before.scheduled_at

        updated_match = await self.repo.update_match(
            organization_id=organization_id,
            match_id=match_id,
            title=title,
            scheduled_at=scheduled_at,
            stream_channel_id=stream_channel_id,
            comment=comment,
        )

        if not updated_match:
            return None

        # Emit MatchScheduledEvent if scheduled_at was changed
        if scheduled_at is not None and scheduled_at != previous_scheduled_at:
            # Fetch participants
            await updated_match.fetch_related('players__user', 'tournament')
            participant_ids = [p.user_id for p in updated_match.players]

            await EventBus.emit(MatchScheduledEvent(
                user_id=user.id if user else None,
                organization_id=organization_id,
                entity_id=match_id,
                tournament_id=updated_match.tournament_id,
                scheduled_time=scheduled_at.isoformat() if scheduled_at else None,
                participant_ids=participant_ids,
            ))
            logger.info("Emitted MatchScheduledEvent for match %s in org %s", match_id, organization_id)

        # Emit events for channel assignment changes
        if stream_channel_id is not None:
            if stream_channel_id != previous_channel_id:
                if stream_channel_id:
                    # Channel assigned or changed
                    channel_name = None
                    if updated_match.stream_channel_id:
                        # Fetch channel name if available
                        await updated_match.fetch_related('stream_channel')
                        if updated_match.stream_channel:
                            channel_name = updated_match.stream_channel.name
                    
                    await EventBus.emit(MatchChannelAssignedEvent(
                        user_id=user.id if user else None,
                        organization_id=organization_id,
                        entity_id=match_id,
                        match_id=match_id,
                        stream_channel_id=stream_channel_id,
                        stream_channel_name=channel_name,
                    ))
                else:
                    # Channel unassigned (set to None)
                    await EventBus.emit(MatchChannelUnassignedEvent(
                        user_id=user.id if user else None,
                        organization_id=organization_id,
                        entity_id=match_id,
                        match_id=match_id,
                        previous_stream_channel_id=previous_channel_id,
                    ))
        
        return updated_match

    async def create_racetime_room(
        self,
        user: Optional[User],
        organization_id: int,
        match_id: int,
    ) -> Optional[Match]:
        """Create a RaceTime.gg room for a match.

        Requires TOURNAMENT_MANAGER permission or MODERATOR permission.

        Args:
            user: User performing the action
            organization_id: Organization ID
            match_id: Match ID

        Returns:
            Updated match with room slug, or None if unauthorized/failed
        """
        # Check if user can manage tournaments (tournament admin) or is a moderator
        can_manage = await self.org_service.user_can_manage_tournaments(user, organization_id)

        if not can_manage:
            # Check if user is at least a moderator
            from application.services.authorization_service import AuthorizationService
            auth_z = AuthorizationService()
            if not auth_z.can_moderate(user):
                logger.warning("Unauthorized create_racetime_room by user %s for org %s", getattr(user, 'id', None), organization_id)
                return None

        # Get match and tournament details
        match = await Match.filter(
            id=match_id,
            tournament__organization_id=organization_id
        ).select_related('tournament__racetime_bot').prefetch_related('players__user').first()

        if not match:
            logger.warning("Match %s not found in org %s", match_id, organization_id)
            return None

        # Verify tournament has RaceTime integration
        if not match.tournament.racetime_bot_id:
            logger.warning("Tournament %s has no RaceTime bot configured", match.tournament_id)
            raise ValueError("Tournament does not have RaceTime integration configured")

        # Check if room already exists
        if match.racetime_room_slug:
            logger.warning("Match %s already has a RaceTime room: %s", match_id, match.racetime_room_slug)
            raise ValueError(f"Match already has a room: {match.racetime_room_slug}")

        # Determine goal (use match-specific or tournament default)
        goal = match.racetime_goal or match.tournament.racetime_default_goal or "Beat the game"

        # Create room via RaceTime bot
        try:
            from racetime.client import RacetimeBot
            import aiohttp
            
            # Get bot credentials
            bot_config = match.tournament.racetime_bot
            
            logger.info("Creating RaceTime room for match %s using bot %s (%s)", 
                       match_id, bot_config.category, bot_config.client_id)
            
            # Create bot instance
            racetime_bot = RacetimeBot(
                category_slug=bot_config.category,
                client_id=bot_config.client_id,
                client_secret=bot_config.client_secret,
                bot_id=bot_config.id
            )
            
            # Initialize the bot's HTTP session and get access token
            racetime_bot.http = aiohttp.ClientSession()
            try:
                logger.info("Authorizing bot with RaceTime API...")
                # Call authorize() directly (not reauthorize which runs in a loop)
                racetime_bot.access_token, racetime_bot.reauthorize_every = racetime_bot.authorize()
                logger.info("Bot authorized successfully, access_token: %s", 
                           racetime_bot.access_token[:20] + "..." if racetime_bot.access_token else "None")
                
                # Create the race room
                logger.info("Creating race room with goal: %s, invitational: %s", 
                           goal, match.racetime_invitational)
                
                # Use race room profile settings if tournament has one configured
                tournament = match.tournament
                
                # Fetch race room profile if configured
                if tournament.race_room_profile_id:
                    await tournament.fetch_related('race_room_profile')
                    profile = tournament.race_room_profile
                    logger.info("Using race room profile %s (%s) for match %s", 
                               profile.id, profile.name, match_id)
                    # Use profile settings
                    start_delay = profile.start_delay
                    time_limit = profile.time_limit
                    streaming_required = profile.streaming_required
                    auto_start = profile.auto_start
                    allow_comments = profile.allow_comments
                    hide_comments = profile.hide_comments
                    allow_prerace_chat = profile.allow_prerace_chat
                    allow_midrace_chat = profile.allow_midrace_chat
                    allow_non_entrant_chat = profile.allow_non_entrant_chat
                else:
                    logger.info("No race room profile configured for tournament %s, using defaults", 
                               tournament.id)
                    # Use default settings
                    start_delay = 15
                    time_limit = 24
                    streaming_required = False
                    auto_start = True
                    allow_comments = True
                    hide_comments = False
                    allow_prerace_chat = True
                    allow_midrace_chat = True
                    allow_non_entrant_chat = True
                
                handler = await racetime_bot.startrace(
                    custom_goal=goal,
                    invitational=match.racetime_invitational,
                    unlisted=False,
                    info_user=match.title or f"Match #{match_id}",
                    start_delay=start_delay,
                    time_limit=time_limit,
                    streaming_required=streaming_required,
                    auto_start=auto_start,
                    allow_comments=allow_comments,
                    hide_comments=hide_comments,
                    allow_prerace_chat=allow_prerace_chat,
                    allow_midrace_chat=allow_midrace_chat,
                    allow_non_entrant_chat=allow_non_entrant_chat,
                )
                
                logger.info("startrace() returned: %s", handler)
                
                if not handler:
                    raise ValueError("Failed to create race room - bot returned None")
                
                # Get room slug from handler
                room_slug = handler.data.get('name')
                logger.info("Room slug from handler: %s", room_slug)
                
                if not room_slug:
                    raise ValueError("Race room created but no slug returned")
                
                # Update match with room details
                match.racetime_room_slug = room_slug
                match.racetime_goal = goal
                await match.save()
                
                logger.info("Created RaceTime room %s for match %s", room_slug, match_id)
                return match
                
            finally:
                # Always close the HTTP session
                if racetime_bot.http and not racetime_bot.http.closed:
                    await racetime_bot.http.close()
                    logger.info("Closed RaceTime bot HTTP session")

        except Exception as e:
            logger.error("Failed to create RaceTime room for match %s: %s", match_id, e, exc_info=True)
            raise

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

    async def process_match_race_finish(
        self,
        match_id: int,
        results: List[dict],
    ) -> bool:
        """
        Process race finish event from RaceTime.gg for a match.

        Updates match player finish ranks based on race results.
        This is called automatically by MatchRaceHandler when a race finishes.

        Args:
            match_id: Match that finished
            results: List of dicts with keys:
                - racetime_id: RaceTime.gg user ID
                - status: Entrant status ('finished', 'forfeit', 'disqualified')
                - finish_time: Finish time (if finished)
                - place: Finishing place (1, 2, 3, etc.)

        Returns:
            True if results were processed successfully, False otherwise
        """
        try:
            # Get the match
            match = await Match.get_or_none(id=match_id).prefetch_related(
                'tournament',
                'players__user'
            )
            if not match:
                logger.warning("Match %s not found when processing race finish", match_id)
                return False

            # Map RaceTime.gg IDs to User IDs
            racetime_ids = [r['racetime_id'] for r in results if r.get('racetime_id')]
            users_map = {
                u.racetime_id: u
                for u in await User.filter(racetime_id__in=racetime_ids).all()
            }

            # Update match player records with finish ranks
            updated_count = 0
            for result in results:
                racetime_id = result.get('racetime_id')
                status = result.get('status')
                place = result.get('place')

                if not racetime_id:
                    continue

                user = users_map.get(racetime_id)
                if not user:
                    logger.warning(
                        "User with RaceTime ID %s not found in match %s results",
                        racetime_id,
                        match_id
                    )
                    continue

                # Only record finish rank for players who finished
                # Note: Players who forfeit or are disqualified do not receive a finish rank
                # since they did not complete the race. Their status is tracked in the
                # race results but not reflected in finish_rank field.
                if status != 'finished' or place is None:
                    logger.debug(
                        "Skipping result for user %s (status: %s, place: %s)",
                        user.id,
                        status,
                        place
                    )
                    continue

                # Find and update the match player record
                match_player = await MatchPlayers.get_or_none(
                    match_id=match_id,
                    user_id=user.id
                )
                if not match_player:
                    logger.warning(
                        "Match player record not found for user %s in match %s",
                        user.id,
                        match_id
                    )
                    continue

                # Update finish rank
                match_player.finish_rank = place
                await match_player.save(update_fields=['finish_rank'])
                updated_count += 1

                logger.info(
                    "Updated match %s player %s with finish rank %s",
                    match_id,
                    user.id,
                    place
                )

            # Mark match as finished
            match.finished_at = datetime.now(timezone.utc)
            await match.save(update_fields=['finished_at'])

            logger.info(
                "Match %s race finished - updated %s player finish ranks",
                match_id,
                updated_count
            )

            # Emit match finished event
            await EventBus.emit(MatchFinishedEvent(
                user_id=SYSTEM_USER_ID,  # System action (automated)
                organization_id=match.tournament.organization_id,
                entity_id=match_id,
                match_id=match_id,
                tournament_id=match.tournament_id,
                finisher_count=updated_count,
            ))

            return True

        except Exception as e:
            logger.error(
                "Failed to process match race finish for match %s: %s",
                match_id,
                e,
                exc_info=True
            )
            return False
