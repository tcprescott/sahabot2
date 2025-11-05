"""
RaceTime Room Service.

This service handles creating and managing RaceTime.gg race rooms for tournament matches.

IMPLEMENTATION NOTE: This service uses patterns from the original SahasrahBot, which relied
on a forked version of racetime-bot (https://github.com/tcprescott/racetime-bot) that added
custom methods like startrace() and join_race_room() to the Bot class, and invite_user() and
send_message() to the RaceHandler class.

Our RacetimeBot client (racetime/client.py) implements these same patterns to maintain
compatibility with the original workflow, even though we're using the upstream racetime-bot
library.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from models import Match, Tournament, User
from racetime.client import get_racetime_bot_instance
from application.events import EventBus, RacetimeRoomCreatedEvent

logger = logging.getLogger(__name__)


class RacetimeRoomService:
    """
    Service for managing RaceTime.gg race rooms.
    
    Handles room creation, player invitations, and room management for tournament matches.
    """
    
    async def create_race_room_for_match(
        self,
        match: Match,
        tournament: Tournament,
        current_user: User,
    ) -> Optional[str]:
        """
        Create a RaceTime.gg race room for a tournament match.
        
        Args:
            match: The match to create a room for
            tournament: The tournament the match belongs to
            current_user: The user creating the room

        Returns:
            Room slug (e.g., "alttpr/cool-doge-1234") or None on failure
        """
        # Validation
        if not tournament.racetime_bot_id:
            logger.error("Tournament %s has no RaceTime bot configured", tournament.id)
            return None
        
        # Load the racetime bot relation
        await tournament.fetch_related('racetime_bot')
        bot_config = tournament.racetime_bot
        
        if not bot_config or not bot_config.is_active:
            logger.error("Tournament %s has inactive or missing RaceTime bot", tournament.id)
            return None
        
        # Get the bot instance
        bot = get_racetime_bot_instance(bot_config.category)
        if not bot:
            logger.error("No running bot instance for category %s", bot_config.category)
            return None
        
        # Load match relations
        await match.fetch_related('players__user', 'tournament')

        # Validate all players have RaceTime linked (if required)
        players = await match.players.all().prefetch_related('user')
        racetime_ids = []

        for match_player in players:
            user = match_player.user
            if not user.racetime_id:
                if tournament.require_racetime_link:
                    logger.error(
                        "Player %s (%s) does not have RaceTime account linked",
                        user.discord_username,
                        user.id
                    )
                    return None
                else:
                    logger.warning(
                        "Player %s (%s) does not have RaceTime account linked (not required)",
                        user.discord_username,
                        user.id
                    )
            else:
                racetime_ids.append(user.racetime_id)

        # Determine race goal
        goal = match.racetime_goal or tournament.racetime_default_goal
        custom_goal = None

        # If no standard goal is set, use a custom goal
        if not goal:
            custom_goal = "Beat the game"

        # Build race info string
        race_info = self._build_race_info(match, tournament)

        # Create the race room using startrace (follows fork pattern)
        try:
            handler = await bot.startrace(
                goal=goal,
                custom_goal=custom_goal,
                invitational=match.racetime_invitational,
                unlisted=False,
                info_user=race_info,
                start_delay=15,
                time_limit=24,
                streaming_required=True,
                auto_start=True,
                allow_comments=True,
                hide_comments=True,
                allow_prerace_chat=True,
                allow_midrace_chat=True,
                allow_non_entrant_chat=False,
                chat_message_delay=0,
                team_race=False,
            )

            if not handler:
                logger.error("Failed to create race room for match %s", match.id)
                return None

            # Replace generic handler with MatchRaceHandler for automatic result recording
            from racetime.match_race_handler import MatchRaceHandler
            
            # If not already a MatchRaceHandler, replace it
            if not isinstance(handler, MatchRaceHandler):
                # Stop the generic handler
                handler.should_stop = True
                
                # Extract race data from the handler
                race_data = handler.data
                
                # Create new match race handler using bot's handler creation pattern
                # The bot.create_handler() would normally be called, but we need our custom class
                # So we instantiate it directly with the same arguments
                match_handler = MatchRaceHandler(
                    match_id=match.id,
                    bot_instance=bot,
                    race_data=race_data,
                    race_logger=logger,
                )
                # Mark that bot created this room
                match_handler._bot_created_room = True
                
                # Initialize the new handler
                await match_handler.begin()
                
                # Use the new handler
                handler = match_handler

            # Extract room slug from handler data
            room_slug = handler.data.get('name')  # e.g., "alttpr/cool-doge-1234"

            # Update match with room info
            match.racetime_room_slug = room_slug
            await match.save(update_fields=['racetime_room_slug'])

            logger.info("Created race room %s for match %s", room_slug, match.id)

            # Invite players to the room using handler's invite_user method
            invited_count = 0
            for racetime_id in racetime_ids:
                try:
                    await handler.invite_user(racetime_id)
                    invited_count += 1
                    logger.debug("Invited user %s to race room %s", racetime_id, room_slug)
                except Exception as e:
                    logger.error("Failed to invite user %s: %s", racetime_id, e)

            logger.info("Invited %d/%d players to race room %s", invited_count, len(racetime_ids), room_slug)

            # Emit event for room creation
            await EventBus.emit(RacetimeRoomCreatedEvent(
                user_id=current_user.id,
                organization_id=tournament.organization_id,
                entity_id=match.id,
                match_id=match.id,
                tournament_id=tournament.id,
                room_slug=room_slug,
                goal=goal or custom_goal,
                player_count=len(players),
                invited_count=invited_count,
            ))

            return room_slug

        except Exception as e:
            logger.error("Error creating race room for match %s: %s", match.id, e, exc_info=True)
            return None
    
    async def send_room_message(
        self,
        room_slug: str,
        message: str,
        category: str,
    ) -> bool:
        """
        Send a message to a RaceTime.gg race room.
        
        Args:
            room_slug: The room slug (e.g., "alttpr/cool-doge-1234")
            message: The message to send
            category: The racetime category (e.g., "alttpr")
            
        Returns:
            True if message sent successfully, False otherwise
        """
        bot = get_racetime_bot_instance(category)
        if not bot:
            logger.error("No running bot instance for category %s", category)
            return False

        try:
            # Join the race room to get a handler
            # Uses our join_race_room implementation (simplified version of fork's method)
            handler = await bot.join_race_room(room_slug, force=False)
            if not handler:
                logger.error("Failed to join race room %s", room_slug)
                return False

            # Send message using handler's method
            await handler.send_message(message)
            logger.info("Sent message to race room %s", room_slug)
            return True

        except Exception as e:
            logger.error("Failed to send message to race room %s: %s", room_slug, e)
            return False
    
    def _build_race_info(self, match: Match, tournament: Tournament) -> str:
        """
        Build the race info string for display in the race room.
        
        Args:
            match: The match
            tournament: The tournament
            
        Returns:
            Race info string
        """
        info_parts = [tournament.name]

        if match.title:
            info_parts.append(f" - {match.title}")

        if match.scheduled_at:
            # Format scheduled time in user-friendly format
            scheduled = match.scheduled_at.strftime("%Y-%m-%d %H:%M UTC")
            info_parts.append(f" - Scheduled: {scheduled}")

        return "".join(info_parts)
    
    async def should_create_room_for_match(self, match: Match) -> bool:
        """
        Check if a race room should be created for this match.

        Args:
            match: The match to check

        Returns:
            True if room should be created, False otherwise
        """
        # Don't create if room already exists
        if match.racetime_room_slug:
            return False
        
        # Don't create if match not scheduled
        if not match.scheduled_at:
            return False
        
        # Don't create if auto-create is disabled for this match
        if not match.racetime_auto_create:
            return False
        
        # Load tournament
        await match.fetch_related('tournament__racetime_bot')
        tournament = match.tournament
        
        # Don't create if tournament doesn't have auto-create enabled
        if not tournament.racetime_auto_create_rooms:
            return False
        
        # Don't create if no bot configured
        if not tournament.racetime_bot_id:
            return False
        
        # Check if bot is active
        if not tournament.racetime_bot.is_active:
            return False
        
        # Check if it's time to create the room
        now = datetime.now(timezone.utc)
        time_until_match = (match.scheduled_at - now).total_seconds() / 60  # minutes
        
        # Create room if we're within the configured window
        if time_until_match <= tournament.room_open_minutes_before and time_until_match > 0:
            return True
        
        return False
