"""
SpeedGaming ETL (Extract, Transform, Load) service.

This service handles importing SpeedGaming episodes into the Match table,
including player and crew member matching/creation.
"""

import logging
from typing import Optional, List, Tuple

from models import User
from models.match_schedule import (
    Tournament,
    Match,
    MatchPlayers,
    Crew,
    CrewRole,
)
from models.organizations import Organization
from application.services.speedgaming_service import (
    SpeedGamingService,
    SpeedGamingEpisode,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
)
from application.repositories.tournament_repository import TournamentRepository
from application.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class SpeedGamingETLService:
    """
    Service for importing SpeedGaming episodes into Match records.

    Handles the ETL process:
    - Extract: Fetch episodes from SpeedGaming API
    - Transform: Map episode data to Match model
    - Load: Create/update Match, MatchPlayers, and Crew records
    """

    def __init__(self):
        """Initialize the SpeedGaming ETL service."""
        self.sg_service = SpeedGamingService()
        self.tournament_repo = TournamentRepository()
        self.user_repo = UserRepository()

    async def _find_or_create_user(
        self,
        organization_id: int,
        sg_player: SpeedGamingPlayer,
    ) -> User:
        """
        Find existing user by Discord ID or create placeholder user.

        Priority:
        1. Match by discord_id (if available)
        2. Create placeholder user with display name from SpeedGaming

        Args:
            organization_id: Organization ID to add user to
            sg_player: SpeedGaming player data

        Returns:
            User object (existing or newly created)
        """
        # Try to find user by Discord ID
        if sg_player.discord_id_int:
            user = await User.get_or_none(discord_id=sg_player.discord_id_int)
            if user:
                logger.info(
                    "Matched player '%s' to existing user %s",
                    sg_player.display_name,
                    user.id
                )

                # Ensure user is a member of the organization
                org = await Organization.get(id=organization_id)
                if not await org.members.filter(id=user.id).exists():
                    await org.members.add(user)
                    logger.info(
                        "Added user %s to organization %s",
                        user.id,
                        organization_id
                    )

                return user

        # Create placeholder user
        # Use a unique identifier based on SG player ID to avoid duplicates
        placeholder_username = f"sg_{sg_player.id}"

        # Check if placeholder already exists
        user = await User.get_or_none(discord_username=placeholder_username)
        if user:
            logger.info(
                "Found existing placeholder user for SG player %s",
                sg_player.id
            )
            return user

        # Determine best display name
        # Priority: streaming_from (Twitch), public_stream, display_name
        display_name = (
            sg_player.streaming_from
            or sg_player.public_stream
            or sg_player.display_name
            or placeholder_username
        )

        # Create new placeholder user
        user = await User.create(
            discord_id=0,  # Placeholder Discord ID
            discord_username=placeholder_username,
            discord_discriminator="0000",
            discord_avatar_hash=None,
            discord_email=None,
            display_name=display_name,
            is_placeholder=True,  # Mark as placeholder
        )
        logger.info(
            "Created placeholder user %s for SpeedGaming player '%s' "
            "(ID: %s, display_name: %s)",
            user.id,
            sg_player.display_name,
            sg_player.id,
            display_name
        )

        # Add to organization
        org = await Organization.get(id=organization_id)
        await org.members.add(user)
        logger.info(
            "Added placeholder user %s to organization %s",
            user.id,
            organization_id
        )

        return user

    async def _find_or_create_crew_user(
        self,
        organization_id: int,
        sg_crew: SpeedGamingCrewMember,
    ) -> User:
        """
        Find existing user by Discord ID or create placeholder user for crew.

        Args:
            organization_id: Organization ID to add user to
            sg_crew: SpeedGaming crew member data

        Returns:
            User object (existing or newly created)
        """
        # Try to find user by Discord ID
        if sg_crew.discord_id_int:
            user = await User.get_or_none(discord_id=sg_crew.discord_id_int)
            if user:
                logger.info(
                    "Matched crew '%s' to existing user %s",
                    sg_crew.display_name,
                    user.id
                )

                # Ensure user is a member of the organization
                org = await Organization.get(id=organization_id)
                if not await org.members.filter(id=user.id).exists():
                    await org.members.add(user)
                    logger.info(
                        "Added crew user %s to organization %s",
                        user.id,
                        organization_id
                    )

                return user

        # Create placeholder user
        # Use a unique identifier based on SG crew ID to avoid duplicates
        placeholder_username = f"sg_crew_{sg_crew.id}"

        # Check if placeholder already exists
        user = await User.get_or_none(discord_username=placeholder_username)
        if user:
            logger.info(
                "Found existing placeholder crew user for SG crew %s",
                sg_crew.id
            )
            return user

        # Determine best display name
        # Priority: public_stream (Twitch), display_name
        display_name = (
            sg_crew.public_stream
            or sg_crew.display_name
            or placeholder_username
        )

        # Create new placeholder user
        user = await User.create(
            discord_id=0,
            discord_username=placeholder_username,
            discord_discriminator="0000",
            discord_avatar_hash=None,
            discord_email=None,
            display_name=display_name,
            is_placeholder=True,
        )
        logger.info(
            "Created placeholder crew user %s for SpeedGaming crew '%s' "
            "(ID: %s, display_name: %s)",
            user.id,
            sg_crew.display_name,
            sg_crew.id,
            display_name
        )

        # Add to organization
        org = await Organization.get(id=organization_id)
        await org.members.add(user)
        logger.info(
            "Added placeholder crew user %s to organization %s",
            user.id,
            organization_id
        )

        return user

    async def import_episode(
        self,
        tournament: Tournament,
        episode: SpeedGamingEpisode,
    ) -> Optional[Match]:
        """
        Import a SpeedGaming episode as a Match record.

        Creates or updates:
        - Match record
        - MatchPlayers records
        - Crew records (commentators, trackers)

        Args:
            tournament: Tournament to import into
            episode: SpeedGaming episode data

        Returns:
            Match object if successful, None if episode should be skipped
        """
        # Check if match already exists
        existing_match = await Match.get_or_none(speedgaming_episode_id=episode.id)
        
        if existing_match:
            logger.info("Episode %s already imported as match %s, skipping", episode.id, existing_match.id)
            return existing_match

        # Get organization ID from tournament
        await tournament.fetch_related('organization')
        organization_id = tournament.organization_id

        # Collect all players from match1 and match2
        all_players: List[SpeedGamingPlayer] = []
        if episode.match1:
            all_players.extend(episode.match1.players)
        if episode.match2:
            all_players.extend(episode.match2.players)

        if not all_players:
            logger.warning("Episode %s has no players, skipping import", episode.id)
            return None

        # Create match
        match_title = episode.title or (episode.match1.title if episode.match1 else "Untitled Match")
        
        match = await Match.create(
            tournament=tournament,
            speedgaming_episode_id=episode.id,
            scheduled_at=episode.when,
            title=match_title,
            comment=f"Imported from SpeedGaming (Episode {episode.id})",
            racetime_auto_create=tournament.racetime_auto_create_rooms,
        )
        logger.info("Created match %s for episode %s", match.id, episode.id)

        # Add players
        for sg_player in all_players:
            user = await self._find_or_create_user(organization_id, sg_player)

            await MatchPlayers.create(
                match=match,
                user=user,
            )
            logger.info("Added player %s to match %s", user.id, match.id)

        # Add commentators (only if approved)
        approved_commentators = 0
        for sg_commentator in episode.commentators:
            if not sg_commentator.approved:
                logger.info(
                    "Skipping unapproved commentator '%s' for match %s",
                    sg_commentator.display_name,
                    match.id
                )
                continue

            user = await self._find_or_create_crew_user(
                organization_id,
                sg_commentator
            )

            await Crew.create(
                match=match,
                user=user,
                role=CrewRole.COMMENTATOR,
                approved=True,
            )
            approved_commentators += 1
            logger.info("Added commentator %s to match %s", user.id, match.id)

        # Add trackers (only if approved)
        approved_trackers = 0
        for sg_tracker in episode.trackers:
            if not sg_tracker.approved:
                logger.info(
                    "Skipping unapproved tracker '%s' for match %s",
                    sg_tracker.display_name,
                    match.id
                )
                continue

            user = await self._find_or_create_crew_user(
                organization_id,
                sg_tracker
            )

            await Crew.create(
                match=match,
                user=user,
                role=CrewRole.TRACKER,
                approved=True,
            )
            approved_trackers += 1
            logger.info("Added tracker %s to match %s", user.id, match.id)

        logger.info(
            "Successfully imported episode %s as match %s with %s players, "
            "%s commentators, %s trackers",
            episode.id,
            match.id,
            len(all_players),
            approved_commentators,
            approved_trackers
        )

        return match

    async def import_episodes_for_tournament(self, tournament_id: int) -> Tuple[int, int]:
        """
        Import all upcoming SpeedGaming episodes for a tournament.

        Args:
            tournament_id: Tournament ID

        Returns:
            Tuple of (imported_count, skipped_count)
        """
        tournament = await Tournament.get_or_none(id=tournament_id)
        if not tournament:
            logger.error("Tournament %s not found", tournament_id)
            return (0, 0)

        if not tournament.speedgaming_enabled:
            logger.info("SpeedGaming integration disabled for tournament %s", tournament_id)
            return (0, 0)

        if not tournament.speedgaming_event_slug:
            logger.warning("Tournament %s has no SpeedGaming event slug configured", tournament_id)
            return (0, 0)

        # Fetch episodes from SpeedGaming
        try:
            episodes = await self.sg_service.get_upcoming_episodes_by_event(
                tournament.speedgaming_event_slug
            )
        except Exception as e:
            logger.error("Failed to fetch episodes for tournament %s: %s", tournament_id, e)
            return (0, 0)

        imported_count = 0
        skipped_count = 0

        for episode in episodes:
            try:
                match = await self.import_episode(tournament, episode)
                if match:
                    imported_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error("Failed to import episode %s: %s", episode.id, e)
                skipped_count += 1

        logger.info(
            "Completed import for tournament %s: %s imported, %s skipped",
            tournament_id,
            imported_count,
            skipped_count
        )

        return (imported_count, skipped_count)

    async def import_all_enabled_tournaments(self) -> Tuple[int, int]:
        """
        Import episodes for all tournaments with SpeedGaming enabled.

        Returns:
            Tuple of (total_imported, total_skipped)
        """
        tournaments = await Tournament.filter(
            speedgaming_enabled=True,
            is_active=True
        ).all()

        total_imported = 0
        total_skipped = 0

        for tournament in tournaments:
            imported, skipped = await self.import_episodes_for_tournament(tournament.id)
            total_imported += imported
            total_skipped += skipped

        logger.info(
            "Completed import for all tournaments: %s imported, %s skipped",
            total_imported,
            total_skipped
        )

        return (total_imported, total_skipped)
