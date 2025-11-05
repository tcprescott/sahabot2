"""
Service for managing Discord scheduled events for tournament matches.

Handles creation, updates, and deletion of Discord's native scheduled events
that appear in the Events section of Discord servers.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord

from models import Match, Tournament, DiscordScheduledEvent, SYSTEM_USER_ID, DiscordEventFilter
from application.repositories.discord_scheduled_event_repository import DiscordScheduledEventRepository
from application.repositories.tournament_repository import TournamentRepository
from application.services.discord_guild_service import DiscordGuildService
from discordbot.client import get_bot_instance

logger = logging.getLogger(__name__)


class DiscordScheduledEventService:
    """Business logic for Discord scheduled events."""

    def __init__(self):
        self.repo = DiscordScheduledEventRepository()
        self.tournament_repo = TournamentRepository()
        self.guild_service = DiscordGuildService()

    async def create_event_for_match(
        self,
        user_id: Optional[int],
        organization_id: int,
        match_id: int,
    ) -> Optional[DiscordScheduledEvent]:
        """
        Create a Discord scheduled event for a match.

        Args:
            user_id: User ID triggering the creation (or SYSTEM_USER_ID)
            organization_id: Organization ID for tenant scoping
            match_id: Match ID to create event for

        Returns:
            Created DiscordScheduledEvent if successful, None otherwise
        """
        # Fetch the match with related data
        match = await Match.get_or_none(
            id=match_id,
            tournament__organization_id=organization_id,
        ).prefetch_related('tournament', 'players__user', 'stream_channel')

        if not match:
            logger.warning("Match %s not found in org %s", match_id, organization_id)
            return None

        # Check if match has a scheduled time
        if not match.scheduled_at:
            logger.debug("Match %s has no scheduled_at time, skipping event creation", match_id)
            return None

        # Check if tournament has Discord events enabled
        tournament = match.tournament
        if not tournament.create_scheduled_events or not tournament.scheduled_events_enabled:
            logger.debug(
                "Discord events not enabled for tournament %s (create=%s, enabled=%s)",
                tournament.id,
                tournament.create_scheduled_events,
                tournament.scheduled_events_enabled,
            )
            return None

        # Check if match passes the event creation filter
        if not self._should_create_event_for_match(match, tournament):
            logger.debug(
                "Match %s does not pass filter %s, skipping event creation",
                match_id,
                tournament.discord_event_filter,
            )
            return None

        # Check if event already exists
        existing_event = await self.repo.get_by_match(organization_id, match_id)
        if existing_event:
            logger.debug("Discord event already exists for match %s", match_id)
            return existing_event

        # Get Discord guild for organization
        await tournament.fetch_related('discord_event_guilds')
        
        # Use configured guilds if any, otherwise fall back to all active guilds for the organization
        if tournament.discord_event_guilds:
            discord_guilds = list(tournament.discord_event_guilds)
        else:
            # Fallback to all active guilds for backwards compatibility
            from models import DiscordGuild
            discord_guilds = await DiscordGuild.filter(organization_id=organization_id, is_active=True).all()
        
        if not discord_guilds:
            logger.warning("No Discord guilds configured for tournament %s in org %s", tournament.id, organization_id)
            return None

        # Get Discord bot instance
        bot = get_bot_instance()
        if not bot:
            logger.error("Discord bot not available")
            return None

        # Format event details (same for all guilds)
        name = self._format_event_name(match, tournament)
        description = self._format_event_description(match, tournament)
        location = await self._format_event_location(match)
        start_time = match.scheduled_at
        end_time = start_time + timedelta(hours=2)  # Default 2-hour duration

        # Track results
        created_events = []
        event_slug = tournament.name[:40] if tournament.name else None

        # Create event in each configured guild
        for discord_guild in discord_guilds:
            try:
                # Get guild from Discord
                guild = bot.get_guild(discord_guild.guild_id)
                if not guild:
                    logger.warning("Discord guild %s not found in bot cache", discord_guild.guild_id)
                    continue

                # Check bot permissions
                if not await self._check_permissions(guild):
                    logger.warning("Bot lacks MANAGE_EVENTS permission in guild %s", guild.id)
                    continue

                # Create Discord scheduled event
                discord_event = await guild.create_scheduled_event(
                    name=name,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    entity_type=discord.EntityType.external,
                    privacy_level=discord.PrivacyLevel.guild_only,
                )

                # Store mapping in database
                db_event = await self.repo.create(
                    scheduled_event_id=discord_event.id,
                    match_id=match_id,
                    organization_id=organization_id,
                    event_slug=event_slug,
                )

                created_events.append(db_event)

                logger.info(
                    "Created Discord event %s in guild %s for match %s (user %s)",
                    discord_event.id,
                    guild.id,
                    match_id,
                    user_id or SYSTEM_USER_ID,
                )

            except discord.Forbidden as e:
                logger.error("Permission denied creating Discord event in guild %s: %s", discord_guild.guild_id, e)
            except discord.HTTPException as e:
                logger.error("HTTP error creating Discord event in guild %s: %s", discord_guild.guild_id, e)
            except Exception as e:
                logger.exception("Unexpected error creating Discord event in guild %s: %s", discord_guild.guild_id, e)

        # Return the first created event (for backwards compatibility)
        # In the future, we might want to return all created events
        return created_events[0] if created_events else None

    async def update_event_for_match(
        self,
        user_id: Optional[int],
        organization_id: int,
        match_id: int,
    ) -> bool:
        """
        Update all Discord scheduled events for a match.

        Args:
            user_id: User ID triggering the update (or SYSTEM_USER_ID)
            organization_id: Organization ID for tenant scoping
            match_id: Match ID to update events for

        Returns:
            True if at least one event was updated successfully, False otherwise
        """
        # Get all existing event records for this match
        db_events = await self.repo.list_for_match(organization_id, match_id)
        if not db_events:
            logger.debug("No Discord events found for match %s, creating new ones", match_id)
            # Try to create if they don't exist
            result = await self.create_event_for_match(user_id, organization_id, match_id)
            return result is not None

        # Fetch the match with related data
        match = await Match.get_or_none(
            id=match_id,
            tournament__organization_id=organization_id,
        ).prefetch_related('tournament', 'players__user', 'stream_channel')

        if not match:
            logger.warning("Match %s not found in org %s", match_id, organization_id)
            return False

        # Check if match still passes the event creation filter
        tournament = match.tournament
        if not self._should_create_event_for_match(match, tournament):
            logger.debug(
                "Match %s no longer passes filter %s, deleting existing events",
                match_id,
                tournament.discord_event_filter,
            )
            # Delete existing events since match no longer passes filter
            await self.delete_event_for_match(user_id, organization_id, match_id)
            return False

        # Get Discord bot instance
        bot = get_bot_instance()
        if not bot:
            logger.error("Discord bot not available")
            return False

        # Format updated details (same for all events)
        tournament = match.tournament
        name = self._format_event_name(match, tournament)
        description = self._format_event_description(match, tournament)
        location = await self._format_event_location(match)
        start_time = match.scheduled_at
        end_time = start_time + timedelta(hours=2) if start_time else None

        # Track success
        updated_count = 0
        
        # Update each Discord event
        for db_event in db_events:
            # Find which guild this event belongs to by querying Discord
            discord_event = None
            guild = None
            
            # Try to find the event in all guilds
            from models import DiscordGuild
            guilds = await DiscordGuild.filter(organization_id=organization_id, is_active=True).all()
            
            for discord_guild in guilds:
                try:
                    guild = bot.get_guild(discord_guild.guild_id)
                    if not guild:
                        continue
                    
                    discord_event = await guild.fetch_scheduled_event(db_event.scheduled_event_id)
                    if discord_event:
                        break
                except discord.NotFound:
                    continue
                except Exception:
                    continue
            
            if not discord_event:
                logger.warning("Discord event %s no longer exists, cleaning up", db_event.scheduled_event_id)
                await self.repo.delete_by_id(db_event.id)
                continue

            try:
                # Update the event
                await discord_event.edit(
                    name=name,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                )

                updated_count += 1
                logger.info(
                    "Updated Discord event %s for match %s in guild %s (user %s)",
                    discord_event.id,
                    match_id,
                    guild.id if guild else 'unknown',
                    user_id or SYSTEM_USER_ID,
                )

            except discord.Forbidden as e:
                logger.error("Permission denied updating Discord event %s: %s", db_event.scheduled_event_id, e)
            except discord.HTTPException as e:
                logger.error("HTTP error updating Discord event %s: %s", db_event.scheduled_event_id, e)
            except Exception as e:
                logger.exception("Unexpected error updating Discord event %s: %s", db_event.scheduled_event_id, e)

        return updated_count > 0

    async def delete_event_for_match(
        self,
        user_id: Optional[int],
        organization_id: int,
        match_id: int,
    ) -> bool:
        """
        Delete all Discord scheduled events for a match.

        Args:
            user_id: User ID triggering the deletion (or SYSTEM_USER_ID)
            organization_id: Organization ID for tenant scoping
            match_id: Match ID to delete events for

        Returns:
            True if deleted successfully, False otherwise
        """
        # Get all existing event records for this match
        db_events = await self.repo.list_for_match(organization_id, match_id)
        if not db_events:
            logger.debug("No Discord events found for match %s", match_id)
            return True  # Already gone, consider it success

        # Get Discord bot instance
        bot = get_bot_instance()
        if not bot:
            logger.error("Discord bot not available")
            # Clean up database records anyway
            for db_event in db_events:
                await self.repo.delete_by_id(db_event.id)
            return True

        # Delete each Discord event
        for db_event in db_events:
            # Find which guild this event belongs to
            discord_event = None
            guild = None
            
            # Try to find the event in all guilds
            from models import DiscordGuild
            guilds = await DiscordGuild.filter(organization_id=organization_id, is_active=True).all()
            
            for discord_guild in guilds:
                try:
                    guild = bot.get_guild(discord_guild.guild_id)
                    if not guild:
                        continue
                    
                    discord_event = await guild.fetch_scheduled_event(db_event.scheduled_event_id)
                    if discord_event:
                        break
                except discord.NotFound:
                    continue
                except Exception:
                    continue
            
            try:
                # Delete the Discord event if found
                if discord_event:
                    await discord_event.delete()
                    logger.info(
                        "Deleted Discord event %s for match %s in guild %s (user %s)",
                        db_event.scheduled_event_id,
                        match_id,
                        guild.id if guild else 'unknown',
                        user_id or SYSTEM_USER_ID,
                    )
                else:
                    logger.debug("Discord event %s already deleted", db_event.scheduled_event_id)

            except discord.Forbidden as e:
                logger.error("Permission denied deleting Discord event %s: %s", db_event.scheduled_event_id, e)
            except discord.HTTPException as e:
                logger.error("HTTP error deleting Discord event %s: %s", db_event.scheduled_event_id, e)
            except Exception as e:
                logger.exception("Unexpected error deleting Discord event %s: %s", db_event.scheduled_event_id, e)

            # Clean up database record regardless
            await self.repo.delete_by_id(db_event.id)

        return True

    async def cleanup_orphaned_events(
        self,
        user_id: Optional[int],
        organization_id: int,
    ) -> dict:
        """
        Clean up all orphaned Discord scheduled events for an organization.

        This includes:
        - Events for finished matches
        - Events for tournaments with scheduled events disabled
        - Events for deleted matches

        Args:
            user_id: User ID triggering cleanup (or SYSTEM_USER_ID)
            organization_id: Organization ID for tenant scoping

        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'deleted': 0,
            'errors': 0,
        }

        # Get all orphaned events
        orphaned_events = await self.repo.cleanup_all_orphaned_events(organization_id)

        logger.info(
            "Cleaning up %d orphaned Discord events in org %s (user %s)",
            len(orphaned_events),
            organization_id,
            user_id or SYSTEM_USER_ID,
        )

        for event in orphaned_events:
            try:
                success = await self.delete_event_for_match(
                    user_id=user_id,
                    organization_id=organization_id,
                    match_id=event.match_id,
                )
                if success:
                    stats['deleted'] += 1
                else:
                    stats['errors'] += 1
            except Exception as e:
                logger.exception(
                    "Error cleaning up orphaned event %s (match %s): %s",
                    event.id,
                    event.match_id,
                    e,
                )
                stats['errors'] += 1

        logger.info(
            "Orphaned event cleanup complete for org %s: %d deleted, %d errors",
            organization_id,
            stats['deleted'],
            stats['errors'],
        )
        return stats

    async def sync_tournament_events(
        self,
        user_id: Optional[int],
        organization_id: int,
        tournament_id: int,
    ) -> dict:
        """
        Synchronize Discord events for all matches in a tournament.

        Creates missing events, updates changed events, deletes orphaned events.

        Args:
            user_id: User ID triggering the sync (or SYSTEM_USER_ID)
            organization_id: Organization ID for tenant scoping
            tournament_id: Tournament ID to sync

        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'created': 0,
            'updated': 0,
            'deleted': 0,
            'skipped': 0,
            'errors': 0,
        }

        # Get tournament
        tournament = await self.tournament_repo.get_for_org(organization_id, tournament_id)
        if not tournament:
            logger.warning("Tournament %s not found in org %s", tournament_id, organization_id)
            return stats

        if not tournament.create_scheduled_events or not tournament.scheduled_events_enabled:
            logger.debug("Discord events not enabled for tournament %s", tournament_id)
            return stats

        # Get all upcoming matches for this tournament
        now = datetime.now(timezone.utc)
        future_cutoff = now + timedelta(days=7)

        matches = await Match.filter(
            tournament_id=tournament_id,
            scheduled_at__lte=future_cutoff,
            finished_at__isnull=True,
        ).prefetch_related('players__user', 'stream_channel')

        # Process each match
        for match in matches:
            if not match.scheduled_at:
                stats['skipped'] += 1
                continue

            # Check if match passes the event creation filter
            if not self._should_create_event_for_match(match, tournament):
                stats['skipped'] += 1
                continue

            # Check if events exist for this match
            existing_events = await self.repo.list_for_match(organization_id, match.id)

            if existing_events:
                # Update existing events
                success = await self.update_event_for_match(user_id, organization_id, match.id)
                if success:
                    stats['updated'] += 1
                else:
                    stats['errors'] += 1
            else:
                # Create new events
                result = await self.create_event_for_match(user_id, organization_id, match.id)
                if result:
                    stats['created'] += 1
                else:
                    # If result is None, it might be skipped due to missing data (e.g., no guilds configured)
                    # This is not necessarily an error, so we'll count it as skipped
                    stats['skipped'] += 1

        # Clean up orphaned events (for finished matches)
        orphaned_events = await self.repo.list_orphaned_events(organization_id)
        for event in orphaned_events:
            success = await self.delete_event_for_match(user_id, organization_id, event.match_id)
            if success:
                stats['deleted'] += 1
            else:
                stats['errors'] += 1

        logger.info(
            "Synced Discord events for tournament %s in org %s: %s",
            tournament_id,
            organization_id,
            stats,
        )
        return stats

    # Helper methods

    def _format_event_name(self, match: Match, tournament: Tournament) -> str:
        """
        Format Discord event name (max 100 characters).

        Format: {TOURNAMENT_NAME} - {MATCH_TITLE or VS_STRING}
        """
        tournament_name = tournament.name[:30] if tournament.name else "Tournament"

        # Use match title if available
        if match.title:
            match_part = match.title[:65]
        else:
            # Build versus string from players
            players = getattr(match, 'players', [])
            if players:
                player_names = [p.user.get_display_name() for p in players[:4]]  # Max 4 players
                match_part = ' vs '.join(player_names[:2])  # Simplify for long names
            else:
                match_part = "Match"

        name = f"{tournament_name} - {match_part}"
        return name[:100]  # Discord's max length

    def _format_event_description(self, match: Match, tournament: Tournament) -> str:
        """Format Discord event description."""
        parts = []

        # Match title or players
        if match.title:
            parts.append(f"**Match:** {match.title}")
        else:
            players = getattr(match, 'players', [])
            if players:
                player_names = [p.user.get_display_name() for p in players]
                parts.append(f"**Players:** {', '.join(player_names)}")

        # Tournament name
        parts.append(f"**Tournament:** {tournament.name}")

        # Stream info
        if match.stream_channel:
            parts.append(f"**Stream:** {match.stream_channel.name}")

        # Match comment if available
        if match.comment:
            parts.append(f"\n{match.comment}")

        return '\n'.join(parts)

    async def _format_event_location(self, match: Match) -> str:
        """
        Format Discord event location (external URL).

        Priority:
        1. Stream channel Twitch URL
        2. Multistream URL if multiple player streams
        3. "TBD"
        """
        # Stream channel takes priority
        if match.stream_channel and match.stream_channel.stream_url:
            return match.stream_channel.stream_url

        # Try to build multistream from player streams
        # (Would need User.twitch_username field - not implemented yet)

        # Default to TBD
        return "TBD"

    async def _check_permissions(self, guild: discord.Guild) -> bool:
        """
        Check if bot has MANAGE_EVENTS permission in guild.

        Args:
            guild: Discord guild to check

        Returns:
            True if bot has permission, False otherwise
        """
        bot_member = guild.me
        if not bot_member:
            return False

        # Check for MANAGE_EVENTS permission (bit 33)
        return bot_member.guild_permissions.manage_events

    def _should_create_event_for_match(self, match: Match, tournament: Tournament) -> bool:
        """
        Check if a match should create a Discord event based on tournament filter.

        Args:
            match: Match to check
            tournament: Tournament the match belongs to

        Returns:
            True if event should be created, False otherwise
        """
        event_filter = tournament.discord_event_filter

        # ALL filter - create event for all scheduled matches
        if event_filter == DiscordEventFilter.ALL:
            return True

        # STREAM_ONLY filter - only create event if match has a stream assigned
        if event_filter == DiscordEventFilter.STREAM_ONLY:
            return match.stream_channel is not None

        # NONE filter - don't create events (same as disabled)
        if event_filter == DiscordEventFilter.NONE:
            return False

        # Default to ALL if unknown filter (shouldn't happen)
        logger.warning("Unknown discord_event_filter: %s, defaulting to ALL", event_filter)
        return True
