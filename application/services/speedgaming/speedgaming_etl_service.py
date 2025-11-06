"""
SpeedGaming ETL (Extract, Transform, Load) service.

This service handles importing SpeedGaming episodes into the Match table,
including player and crew member matching/creation.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from models import User
from models.match_schedule import (
    Tournament,
    Match,
    MatchPlayers,
    Crew,
    CrewRole,
)
from models.organizations import Organization, OrganizationMember
from models.audit_log import AuditLog
from application.services.speedgaming.speedgaming_service import (
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
        Find existing user by Discord ID, username, or SpeedGaming ID, or create placeholder user.

        Priority:
        1. Match by discord_id (if available)
        2. Match by discord_username (from discord_tag if available)
        3. Match by speedgaming_id (for existing placeholders)
        4. Create new placeholder user with display name from SpeedGaming

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
                    "Matched player '%s' to existing user %s by Discord ID",
                    sg_player.display_name,
                    user.id
                )

                # Ensure user is a member of the organization
                member = await OrganizationMember.get_or_none(
                    organization_id=organization_id,
                    user_id=user.id
                )
                if not member:
                    await OrganizationMember.create(
                        organization_id=organization_id,
                        user_id=user.id
                    )
                    logger.info(
                        "Added user %s to organization %s",
                        user.id,
                        organization_id
                    )

                return user

        # Try to find user by Discord username (from discord_tag)
        if sg_player.discord_tag:
            # Parse username from discord_tag (format: "username#discriminator")
            discord_username = sg_player.discord_tag.split("#")[0] if "#" in sg_player.discord_tag else sg_player.discord_tag
            
            if discord_username:
                user = await User.get_or_none(discord_username=discord_username)
                if user:
                    logger.info(
                        "Matched player '%s' to existing user %s by Discord username '%s'",
                        sg_player.display_name,
                        user.id,
                        discord_username
                    )

                    # Ensure user is a member of the organization
                    member = await OrganizationMember.get_or_none(
                        organization_id=organization_id,
                        user_id=user.id
                    )
                    if not member:
                        await OrganizationMember.create(
                            organization_id=organization_id,
                            user_id=user.id
                        )
                        logger.info(
                            "Added user %s to organization %s",
                            user.id,
                            organization_id
                        )

                    return user

        # Try to find placeholder user by SpeedGaming ID
        user = await User.get_or_none(
            is_placeholder=True,
            speedgaming_id=sg_player.id
        )
        
        if user:
            logger.info(
                "Found existing placeholder user for SG player %s",
                sg_player.id
            )
            
            # Update display name if it has changed
            new_display_name = (
                sg_player.streaming_from
                or sg_player.public_stream
                or sg_player.display_name
                or f"sg_{sg_player.id}"
            )
            
            if user.display_name != new_display_name:
                logger.info(
                    "Updating placeholder user %s display name: %s -> %s",
                    user.id,
                    user.display_name,
                    new_display_name
                )
                user.display_name = new_display_name
                await user.save()
            
            return user

        # Create new placeholder user
        # Use a unique identifier based on SG player ID to avoid duplicates
        placeholder_username = f"sg_{sg_player.id}"

        # Determine best display name
        # Priority: streaming_from (Twitch), public_stream, display_name
        display_name = (
            sg_player.streaming_from
            or sg_player.public_stream
            or sg_player.display_name
            or placeholder_username
        )

        # Create new placeholder user
        # Note: discord_id=None for placeholders (no Discord account linked)
        user = await User.create(
            discord_id=None,  # No Discord ID available for placeholder
            discord_username=placeholder_username,
            discord_discriminator="0000",
            discord_avatar_hash=None,
            discord_email=None,
            display_name=display_name,
            is_placeholder=True,  # Primary indicator for placeholder users
            speedgaming_id=sg_player.id,  # Store SpeedGaming ID
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
        await OrganizationMember.create(
            organization_id=organization_id,
            user_id=user.id
        )
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
        Find existing user by Discord ID, username, or SpeedGaming ID, or create placeholder user for crew.

        Priority:
        1. Match by discord_id (if available)
        2. Match by discord_username (from discord_tag if available)
        3. Match by speedgaming_id (for existing placeholders)
        4. Create new placeholder user

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
                    "Matched crew '%s' to existing user %s by Discord ID",
                    sg_crew.display_name,
                    user.id
                )

                # Ensure user is a member of the organization
                member = await OrganizationMember.get_or_none(
                    organization_id=organization_id,
                    user_id=user.id
                )
                if not member:
                    await OrganizationMember.create(
                        organization_id=organization_id,
                        user_id=user.id
                    )
                    logger.info(
                        "Added crew user %s to organization %s",
                        user.id,
                        organization_id
                    )

                return user

        # Try to find user by Discord username (from discord_tag)
        if sg_crew.discord_tag:
            # Parse username from discord_tag (format: "username#discriminator")
            discord_username = sg_crew.discord_tag.split("#")[0] if "#" in sg_crew.discord_tag else sg_crew.discord_tag
            
            if discord_username:
                user = await User.get_or_none(discord_username=discord_username)
                if user:
                    logger.info(
                        "Matched crew '%s' to existing user %s by Discord username '%s'",
                        sg_crew.display_name,
                        user.id,
                        discord_username
                    )

                    # Ensure user is a member of the organization
                    member = await OrganizationMember.get_or_none(
                        organization_id=organization_id,
                        user_id=user.id
                    )
                    if not member:
                        await OrganizationMember.create(
                            organization_id=organization_id,
                            user_id=user.id
                        )
                        logger.info(
                            "Added crew user %s to organization %s",
                            user.id,
                            organization_id
                        )

                    return user

        # Try to find placeholder user by SpeedGaming ID
        user = await User.get_or_none(
            is_placeholder=True,
            speedgaming_id=sg_crew.id
        )
        
        if user:
            logger.info(
                "Found existing placeholder crew user for SG crew %s",
                sg_crew.id
            )
            
            # Update display name if it has changed
            new_display_name = (
                sg_crew.public_stream
                or sg_crew.display_name
                or f"sg_crew_{sg_crew.id}"
            )
            
            if user.display_name != new_display_name:
                logger.info(
                    "Updating placeholder crew user %s display name: %s -> %s",
                    user.id,
                    user.display_name,
                    new_display_name
                )
                user.display_name = new_display_name
                await user.save()
            
            return user

        # Create new placeholder user
        # Use a unique identifier based on SG crew ID to avoid duplicates
        placeholder_username = f"sg_crew_{sg_crew.id}"

        # Determine best display name
        # Priority: public_stream (Twitch), display_name
        display_name = (
            sg_crew.public_stream
            or sg_crew.display_name
            or placeholder_username
        )

        # Create new placeholder user
        # Note: discord_id=None for placeholders (no Discord account linked)
        user = await User.create(
            discord_id=None,  # No Discord ID available for placeholder
            discord_username=placeholder_username,
            discord_discriminator="0000",
            discord_avatar_hash=None,
            discord_email=None,
            display_name=display_name,
            is_placeholder=True,  # Primary indicator for placeholder users
            speedgaming_id=sg_crew.id,  # Store SpeedGaming ID
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
        await OrganizationMember.create(
            organization_id=organization_id,
            user_id=user.id
        )
        logger.info(
            "Added placeholder crew user %s to organization %s",
            user.id,
            organization_id
        )

        return user

    async def _sync_match_players(
        self,
        match: Match,
        sg_players: List[SpeedGamingPlayer],
        organization_id: int
    ) -> None:
        """
        Sync match players with SpeedGaming data.

        Detects added/removed players and updates accordingly.

        Args:
            match: Match to sync
            sg_players: Current players from SpeedGaming
            organization_id: Organization ID
        """
        # Get current players
        current_players = await MatchPlayers.filter(
            match=match
        ).prefetch_related('user').all()

        # Build set of current user IDs (both real and placeholder via SG ID)
        current_user_ids = set()
        current_sg_ids = set()
        
        for mp in current_players:
            current_user_ids.add(mp.user_id)
            if mp.user.is_placeholder and mp.user.speedgaming_id:
                current_sg_ids.add(mp.user.speedgaming_id)
            elif not mp.user.is_placeholder and mp.user.discord_id:
                # Track by discord_id for real users
                pass

        # Build set of new player SpeedGaming IDs and Discord IDs
        new_sg_ids = {p.id for p in sg_players}
        new_discord_ids = {
            p.discord_id_int for p in sg_players if p.discord_id_int
        }

        # Find players to add (in SG but not in current)
        for sg_player in sg_players:
            # Check if this player is already in the match
            already_exists = False
            
            # Check by Discord ID first
            if sg_player.discord_id_int:
                for mp in current_players:
                    if (not mp.user.is_placeholder and 
                        mp.user.discord_id == sg_player.discord_id_int):
                        already_exists = True
                        break
            
            # Check by SpeedGaming ID for placeholders
            if not already_exists and sg_player.id in current_sg_ids:
                already_exists = True
            
            if not already_exists:
                # Add new player
                user = await self._find_or_create_user(organization_id, sg_player)
                await MatchPlayers.create(match=match, user=user)
                logger.info(
                    "Added new player %s to match %s (SG player %s)",
                    user.id,
                    match.id,
                    sg_player.id
                )

        # Find players to remove (in current but not in SG)
        for mp in current_players:
            should_remove = False
            
            if mp.user.is_placeholder and mp.user.speedgaming_id:
                # Placeholder user - check by SG ID
                if mp.user.speedgaming_id not in new_sg_ids:
                    should_remove = True
            elif not mp.user.is_placeholder and mp.user.discord_id:
                # Real user - check by Discord ID
                if mp.user.discord_id not in new_discord_ids:
                    should_remove = True
            
            if should_remove:
                logger.info(
                    "Removing player %s from match %s (no longer in SG episode)",
                    mp.user_id,
                    match.id
                )
                await mp.delete()

    async def _sync_match_crew(
        self,
        match: Match,
        sg_commentators: List[SpeedGamingCrewMember],
        sg_trackers: List[SpeedGamingCrewMember],
        organization_id: int
    ) -> None:
        """
        Sync match crew with SpeedGaming data.

        Detects added/removed crew and updates accordingly.
        Only syncs approved crew members.

        Args:
            match: Match to sync
            sg_commentators: Current commentators from SpeedGaming
            sg_trackers: Current trackers from SpeedGaming
            organization_id: Organization ID
        """
        # Get current crew
        current_crew = await Crew.filter(
            match=match
        ).prefetch_related('user').all()

        # Build current crew sets by role and SG ID
        current_commentator_sg_ids = set()
        current_tracker_sg_ids = set()
        current_crew_by_user = {}
        
        for crew in current_crew:
            current_crew_by_user[crew.user_id] = crew
            if crew.user.is_placeholder and crew.user.speedgaming_id:
                if crew.role == CrewRole.COMMENTATOR:
                    current_commentator_sg_ids.add(crew.user.speedgaming_id)
                elif crew.role == CrewRole.TRACKER:
                    current_tracker_sg_ids.add(crew.user.speedgaming_id)

        # Sync commentators (approved only)
        approved_commentators = [c for c in sg_commentators if c.approved]
        for sg_comm in approved_commentators:
            # Check if already exists
            already_exists = False
            
            if sg_comm.discord_id_int:
                for crew in current_crew:
                    if (crew.role == CrewRole.COMMENTATOR and
                        not crew.user.is_placeholder and
                        crew.user.discord_id == sg_comm.discord_id_int):
                        already_exists = True
                        break
            
            if not already_exists and sg_comm.id in current_commentator_sg_ids:
                already_exists = True
            
            if not already_exists:
                user = await self._find_or_create_crew_user(organization_id, sg_comm)
                await Crew.create(
                    match=match,
                    user=user,
                    role=CrewRole.COMMENTATOR,
                    approved=True
                )
                logger.info(
                    "Added new commentator %s to match %s (SG crew %s)",
                    user.id,
                    match.id,
                    sg_comm.id
                )

        # Sync trackers (approved only)
        approved_trackers = [t for t in sg_trackers if t.approved]
        for sg_tracker in approved_trackers:
            # Check if already exists
            already_exists = False
            
            if sg_tracker.discord_id_int:
                for crew in current_crew:
                    if (crew.role == CrewRole.TRACKER and
                        not crew.user.is_placeholder and
                        crew.user.discord_id == sg_tracker.discord_id_int):
                        already_exists = True
                        break
            
            if not already_exists and sg_tracker.id in current_tracker_sg_ids:
                already_exists = True
            
            if not already_exists:
                user = await self._find_or_create_crew_user(organization_id, sg_tracker)
                await Crew.create(
                    match=match,
                    user=user,
                    role=CrewRole.TRACKER,
                    approved=True
                )
                logger.info(
                    "Added new tracker %s to match %s (SG crew %s)",
                    user.id,
                    match.id,
                    sg_tracker.id
                )

        # Remove crew no longer in SpeedGaming
        approved_comm_sg_ids = {c.id for c in approved_commentators}
        approved_tracker_sg_ids = {t.id for t in approved_trackers}
        approved_comm_discord_ids = {
            c.discord_id_int for c in approved_commentators if c.discord_id_int
        }
        approved_tracker_discord_ids = {
            t.discord_id_int for t in approved_trackers if t.discord_id_int
        }
        
        for crew in current_crew:
            should_remove = False
            
            if crew.role == CrewRole.COMMENTATOR:
                if crew.user.is_placeholder and crew.user.speedgaming_id:
                    if crew.user.speedgaming_id not in approved_comm_sg_ids:
                        should_remove = True
                elif not crew.user.is_placeholder and crew.user.discord_id:
                    if crew.user.discord_id not in approved_comm_discord_ids:
                        should_remove = True
            
            elif crew.role == CrewRole.TRACKER:
                if crew.user.is_placeholder and crew.user.speedgaming_id:
                    if crew.user.speedgaming_id not in approved_tracker_sg_ids:
                        should_remove = True
                elif not crew.user.is_placeholder and crew.user.discord_id:
                    if crew.user.discord_id not in approved_tracker_discord_ids:
                        should_remove = True
            
            if should_remove:
                logger.info(
                    "Removing crew %s (role: %s) from match %s (no longer in SG episode)",
                    crew.user_id,
                    crew.role,
                    match.id
                )
                await crew.delete()

    async def import_episode(
        self,
        tournament: Tournament,
        episode: SpeedGamingEpisode,
    ) -> Optional[Match]:
        """
        Import or update a SpeedGaming episode as a Match record.

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
        existing_match = await Match.get_or_none(
            speedgaming_episode_id=episode.id
        )

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

        # Determine match title
        match_title = episode.title or (
            episode.match1.title if episode.match1 else "Untitled Match"
        )

        if existing_match:
            # Update existing match
            logger.info(
                "Episode %s already exists as match %s, checking for updates",
                episode.id,
                existing_match.id
            )

            # Check if anything changed
            needs_update = False
            if existing_match.scheduled_at != episode.when:
                existing_match.scheduled_at = episode.when
                needs_update = True
                logger.info(
                    "Episode %s schedule changed: %s -> %s",
                    episode.id,
                    existing_match.scheduled_at,
                    episode.when
                )

            if existing_match.title != match_title:
                existing_match.title = match_title
                needs_update = True
                logger.info(
                    "Episode %s title changed: %s -> %s",
                    episode.id,
                    existing_match.title,
                    match_title
                )

            if needs_update:
                await existing_match.save()
                logger.info("Updated match %s for episode %s", existing_match.id, episode.id)

            # Check for player changes
            await self._sync_match_players(
                existing_match,
                all_players,
                organization_id
            )

            # Check for crew changes
            await self._sync_match_crew(
                existing_match,
                episode.commentators,
                episode.trackers,
                organization_id
            )

            return existing_match

        # Create new match
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

    async def import_episodes_for_tournament(
        self,
        tournament_id: int
    ) -> Tuple[int, int, int]:
        """
        Import all upcoming SpeedGaming episodes for a tournament.

        Also detects and removes deleted episodes. Logs sync results to audit log.

        Args:
            tournament_id: Tournament ID

        Returns:
            Tuple of (imported_count, updated_count, deleted_count)
        """
        start_time = datetime.now(timezone.utc)
        tournament = await Tournament.get_or_none(id=tournament_id)
        if not tournament:
            logger.error("Tournament %s not found", tournament_id)
            await self._log_sync_result(
                tournament_id,
                None,
                success=False,
                error="Tournament not found",
                start_time=start_time
            )
            return (0, 0, 0)

        if not tournament.speedgaming_enabled:
            logger.info(
                "SpeedGaming integration disabled for tournament %s",
                tournament_id
            )
            return (0, 0, 0)

        if not tournament.speedgaming_event_slug:
            logger.warning(
                "Tournament %s has no SpeedGaming event slug configured",
                tournament_id
            )
            await self._log_sync_result(
                tournament_id,
                tournament.organization_id,
                success=False,
                error="No event slug configured",
                start_time=start_time
            )
            return (0, 0, 0)

        # Fetch episodes from SpeedGaming
        try:
            episodes = await self.sg_service.get_upcoming_episodes_by_event(
                tournament.speedgaming_event_slug
            )
        except Exception as e:
            logger.error(
                "Failed to fetch episodes for tournament %s: %s",
                tournament_id,
                e
            )
            await self._log_sync_result(
                tournament_id,
                tournament.organization_id,
                success=False,
                error=f"API error: {str(e)}",
                start_time=start_time
            )
            return (0, 0, 0)

        # Track episode IDs from SpeedGaming
        sg_episode_ids = {episode.id for episode in episodes}

        # Import/update episodes
        imported_count = 0
        updated_count = 0
        errors = []

        for episode in episodes:
            try:
                # Check if episode already exists
                existing = await Match.get_or_none(
                    speedgaming_episode_id=episode.id
                )

                match = await self.import_episode(tournament, episode)

                if match:
                    if existing:
                        updated_count += 1
                    else:
                        imported_count += 1

            except Exception as e:
                logger.error("Failed to import episode %s: %s", episode.id, e)
                errors.append(f"Episode {episode.id}: {str(e)}")

        # Detect deleted episodes
        deleted_count = await self._detect_deleted_episodes(
            tournament,
            sg_episode_ids
        )

        logger.info(
            "Completed import for tournament %s: %s imported, "
            "%s updated, %s deleted",
            tournament_id,
            imported_count,
            updated_count,
            deleted_count
        )

        # Log sync result
        await self._log_sync_result(
            tournament_id,
            tournament.organization_id,
            success=len(errors) == 0,
            imported=imported_count,
            updated=updated_count,
            deleted=deleted_count,
            error="; ".join(errors) if errors else None,
            start_time=start_time
        )

        return (imported_count, updated_count, deleted_count)

    async def _log_sync_result(
        self,
        tournament_id: int,
        organization_id: Optional[int],
        success: bool,
        imported: int = 0,
        updated: int = 0,
        deleted: int = 0,
        error: Optional[str] = None,
        start_time: Optional[datetime] = None
    ):
        """
        Log SpeedGaming sync result to audit log.

        Args:
            tournament_id: Tournament ID
            organization_id: Organization ID
            success: Whether sync was successful
            imported: Number of matches imported
            updated: Number of matches updated
            deleted: Number of matches deleted
            error: Error message if sync failed
            start_time: When sync started
        """
        end_time = datetime.now(timezone.utc)
        duration_ms = None
        if start_time:
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

        await AuditLog.create(
            user_id=None,  # System action, no actual user
            organization_id=organization_id,
            action="speedgaming_sync",
            details={
                "tournament_id": tournament_id,
                "success": success,
                "imported": imported,
                "updated": updated,
                "deleted": deleted,
                "error": error,
                "duration_ms": duration_ms,
            }
        )

    async def _log_aggregated_sync_result(
        self,
        success: bool,
        imported: int = 0,
        updated: int = 0,
        deleted: int = 0,
        error: Optional[str] = None,
        start_time: Optional[datetime] = None
    ):
        """
        Log aggregated SpeedGaming sync result across all tournaments to audit log.

        Args:
            success: Whether sync was successful
            imported: Total number of matches imported across all tournaments
            updated: Total number of matches updated across all tournaments
            deleted: Total number of matches deleted across all tournaments
            error: Error message if sync failed
            start_time: When sync started
        """
        end_time = datetime.now(timezone.utc)
        duration_ms = None
        if start_time:
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

        await AuditLog.create(
            user_id=None,  # System action, no actual user
            organization_id=None,  # System-wide, not specific to an organization
            action="speedgaming_sync_all",
            details={
                "tournament_id": None,  # Aggregated across all tournaments
                "success": success,
                "imported": imported,
                "updated": updated,
                "deleted": deleted,
                "error": error,
                "duration_ms": duration_ms,
            }
        )

    async def _detect_deleted_episodes(
        self,
        tournament: Tournament,
        current_episode_ids: set[int]
    ) -> int:
        """
        Detect and delete matches for episodes no longer in SpeedGaming.

        Args:
            tournament: Tournament to check
            current_episode_ids: Set of episode IDs currently in SpeedGaming

        Returns:
            Number of matches deleted
        """
        # Find all matches for this tournament that came from SpeedGaming
        existing_matches = await Match.filter(
            tournament=tournament,
            speedgaming_episode_id__isnull=False
        ).all()

        deleted_count = 0

        for match in existing_matches:
            # If episode ID is not in current list, verify it's deleted
            if match.speedgaming_episode_id not in current_episode_ids:
                # Double-check by querying SpeedGaming API directly
                try:
                    episode = await self.sg_service.get_episode(
                        match.speedgaming_episode_id
                    )

                    if episode is None:
                        # Episode is truly deleted, remove the match
                        logger.info(
                            "Episode %s no longer exists in SpeedGaming, "
                            "deleting match %s",
                            match.speedgaming_episode_id,
                            match.id
                        )
                        await match.delete()
                        deleted_count += 1
                    else:
                        logger.info(
                            "Episode %s still exists but not in event schedule, "
                            "keeping match %s",
                            match.speedgaming_episode_id,
                            match.id
                        )

                except Exception as e:
                    logger.error(
                        "Error checking episode %s: %s",
                        match.speedgaming_episode_id,
                        e
                    )

        return deleted_count

    async def import_all_enabled_tournaments(self) -> Tuple[int, int, int]:
        """
        Import episodes for all tournaments with SpeedGaming enabled.

        Returns:
            Tuple of (total_imported, total_updated, total_deleted)
        """
        start_time = datetime.now(timezone.utc)
        tournaments = await Tournament.filter(
            speedgaming_enabled=True,
            is_active=True
        ).all()

        total_imported = 0
        total_updated = 0
        total_deleted = 0
        errors = []

        for tournament in tournaments:
            try:
                imported, updated, deleted = await self.import_episodes_for_tournament(
                    tournament.id
                )
                total_imported += imported
                total_updated += updated
                total_deleted += deleted
            except Exception as e:
                logger.error(
                    "Error importing episodes for tournament %s: %s",
                    tournament.id,
                    e
                )
                errors.append(f"Tournament {tournament.id}: {str(e)}")

        logger.info(
            "Completed import for all tournaments: %s imported, "
            "%s updated, %s deleted",
            total_imported,
            total_updated,
            total_deleted
        )

        # Log aggregated sync result
        await self._log_aggregated_sync_result(
            success=len(errors) == 0,
            imported=total_imported,
            updated=total_updated,
            deleted=total_deleted,
            error="; ".join(errors) if errors else None,
            start_time=start_time
        )

        return (total_imported, total_updated, total_deleted)
