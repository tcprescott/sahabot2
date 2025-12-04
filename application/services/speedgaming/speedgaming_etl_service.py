"""
SpeedGaming ETL (Extract, Transform, Load) service.

This service handles importing SpeedGaming episodes into the Match table,
including player and crew member matching/creation.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple

from models import User
from modules.tournament.models.match_schedule import (
    Tournament,
    Match,
    MatchPlayers,
    Crew,
    CrewRole,
    StreamChannel,
)
from models.organizations import OrganizationMember
from models.audit_log import AuditLog
from models.racetime_room import RacetimeRoom
from application.services.speedgaming.speedgaming_service import (
    SpeedGamingService,
    SpeedGamingEpisode,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
    SpeedGamingChannel,
)
from modules.tournament.repositories.tournament_repository import TournamentRepository
from application.repositories.user_repository import UserRepository
from modules.tournament.repositories.stream_channel_repository import StreamChannelRepository

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
        self.stream_channel_repo = StreamChannelRepository()

    async def _find_or_create_user(
        self,
        organization_id: int,
        sg_player: SpeedGamingPlayer,
    ) -> User:
        """
        Find existing user by Discord ID, username, or SpeedGaming ID, or create user.

        Priority:
        1. Match by discord_id (if available)
        2. Match by discord_username (from discord_tag if available)
        3. Match by speedgaming_id (for existing placeholders)
        4. Create new user with Discord ID if available, otherwise placeholder

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
                    user.id,
                )

                # Ensure user is a member of the organization
                member = await OrganizationMember.get_or_none(
                    organization_id=organization_id, user_id=user.id
                )
                if not member:
                    await OrganizationMember.create(
                        organization_id=organization_id, user_id=user.id
                    )
                    logger.info(
                        "Added user %s to organization %s", user.id, organization_id
                    )

                return user

        # Try to find user by Discord username (from discord_tag)
        if sg_player.discord_tag:
            # Parse username from discord_tag (format: "username#discriminator")
            discord_username = (
                sg_player.discord_tag.split("#")[0]
                if "#" in sg_player.discord_tag
                else sg_player.discord_tag
            )

            if discord_username:
                user = await User.get_or_none(discord_username=discord_username)
                if user:
                    logger.info(
                        "Matched player '%s' to existing user %s by Discord username '%s'",
                        sg_player.display_name,
                        user.id,
                        discord_username,
                    )

                    # Ensure user is a member of the organization
                    member = await OrganizationMember.get_or_none(
                        organization_id=organization_id, user_id=user.id
                    )
                    if not member:
                        await OrganizationMember.create(
                            organization_id=organization_id, user_id=user.id
                        )
                        logger.info(
                            "Added user %s to organization %s", user.id, organization_id
                        )

                    return user

        # Try to find placeholder user by SpeedGaming ID (might need to upgrade to full user)
        user = await User.get_or_none(is_placeholder=True, speedgaming_id=sg_player.id)

        if user:
            # If we now have a Discord ID, check if a real user with that ID already exists
            if sg_player.discord_id_int:
                # Check if there's already a real user with this Discord ID
                existing_real_user = await User.get_or_none(
                    discord_id=sg_player.discord_id_int, is_placeholder=False
                )

                if existing_real_user:
                    # A real user with this Discord ID exists - use that instead
                    logger.info(
                        "Found existing real user %s with Discord ID %s for placeholder %s (SG player %s)",
                        existing_real_user.id,
                        sg_player.discord_id_int,
                        user.id,
                        sg_player.id,
                    )

                    # TODO: In the future, we could merge the placeholder into the real user
                    # For now, we'll use the real user and leave the placeholder

                    # Ensure real user is a member of the organization
                    member = await OrganizationMember.get_or_none(
                        organization_id=organization_id, user_id=existing_real_user.id
                    )
                    if not member:
                        await OrganizationMember.create(
                            organization_id=organization_id,
                            user_id=existing_real_user.id,
                        )
                        logger.info(
                            "Added existing real user %s to organization %s",
                            existing_real_user.id,
                            organization_id,
                        )

                    return existing_real_user

                # No existing real user - upgrade the placeholder
                if not user.discord_id:
                    logger.info(
                        "Upgrading placeholder user %s to full user with Discord ID %s",
                        user.id,
                        sg_player.discord_id_int,
                    )

                    # Best-effort username from discord_tag
                    discord_username = None
                    if sg_player.discord_tag:
                        discord_username = (
                            sg_player.discord_tag.split("#")[0]
                            if "#" in sg_player.discord_tag
                            else sg_player.discord_tag
                        )

                    if not discord_username:
                        # Fallback: use display name or streaming username
                        discord_username = (
                            sg_player.streaming_from
                            or sg_player.display_name
                            or f"user_{sg_player.discord_id_int}"
                        )

                    user.discord_id = sg_player.discord_id_int
                    user.discord_username = discord_username
                    user.is_placeholder = False  # No longer a placeholder
                    await user.save()

                    logger.info(
                        "Upgraded user %s: discord_id=%s, username=%s",
                        user.id,
                        user.discord_id,
                        user.discord_username,
                    )
                    return user

            # Still a placeholder (no Discord ID provided), just update display name if needed
            logger.info(
                "Found existing placeholder user for SG player %s", sg_player.id
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
                    new_display_name,
                )
                user.display_name = new_display_name
                await user.save()

            return user

        # Create new user
        # If we have a Discord ID, create full user; otherwise create placeholder

        # Determine username
        if sg_player.discord_id_int:
            # We have Discord ID - create full user with best-effort username
            discord_id = sg_player.discord_id_int

            # Try to extract username from discord_tag
            if sg_player.discord_tag:
                discord_username = (
                    sg_player.discord_tag.split("#")[0]
                    if "#" in sg_player.discord_tag
                    else sg_player.discord_tag
                )
            else:
                # Best effort: use streaming name, display name, or generic fallback
                discord_username = (
                    sg_player.streaming_from
                    or sg_player.display_name
                    or f"user_{discord_id}"
                )

            is_placeholder = False
            logger.info(
                "Creating full user with Discord ID %s (username: %s) for SpeedGaming player '%s'",
                discord_id,
                discord_username,
                sg_player.display_name,
            )
        else:
            # No Discord ID - create placeholder
            discord_id = None
            discord_username = f"sg_{sg_player.id}"
            is_placeholder = True
            logger.info(
                "Creating placeholder user for SpeedGaming player '%s' (no Discord ID available)",
                sg_player.display_name,
            )

        # Determine best display name
        # Priority: streaming_from (Twitch), public_stream, display_name
        display_name = (
            sg_player.streaming_from
            or sg_player.public_stream
            or sg_player.display_name
            or discord_username
        )

        # Create user
        user = await User.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=(
                "0000"
                if sg_player.discord_tag and "#" in sg_player.discord_tag
                else None
            ),
            discord_avatar=None,
            discord_email=None,
            display_name=display_name,
            is_placeholder=is_placeholder,
            speedgaming_id=sg_player.id,  # Store SpeedGaming ID for tracking
        )

        user_type = "placeholder" if is_placeholder else "full"
        logger.info(
            "Created %s user %s for SpeedGaming player '%s' "
            "(SG ID: %s, discord_id: %s, display_name: %s)",
            user_type,
            user.id,
            sg_player.display_name,
            sg_player.id,
            discord_id,
            display_name,
        )

        # Add to organization
        await OrganizationMember.create(
            organization_id=organization_id, user_id=user.id
        )
        logger.info("Added user %s to organization %s", user.id, organization_id)

        return user

    async def _find_or_create_crew_user(
        self,
        organization_id: int,
        sg_crew: SpeedGamingCrewMember,
    ) -> User:
        """
        Find existing user by Discord ID, username, or SpeedGaming ID, or create user for crew.

        Priority:
        1. Match by discord_id (if available)
        2. Match by discord_username (from discord_tag if available)
        3. Match by speedgaming_id (for existing placeholders)
        4. Create new user with Discord ID if available, otherwise placeholder

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
                    user.id,
                )

                # Ensure user is a member of the organization
                member = await OrganizationMember.get_or_none(
                    organization_id=organization_id, user_id=user.id
                )
                if not member:
                    await OrganizationMember.create(
                        organization_id=organization_id, user_id=user.id
                    )
                    logger.info(
                        "Added crew user %s to organization %s",
                        user.id,
                        organization_id,
                    )

                return user

        # Try to find user by Discord username (from discord_tag)
        if sg_crew.discord_tag:
            # Parse username from discord_tag (format: "username#discriminator")
            discord_username = (
                sg_crew.discord_tag.split("#")[0]
                if "#" in sg_crew.discord_tag
                else sg_crew.discord_tag
            )

            if discord_username:
                user = await User.get_or_none(discord_username=discord_username)
                if user:
                    logger.info(
                        "Matched crew '%s' to existing user %s by Discord username '%s'",
                        sg_crew.display_name,
                        user.id,
                        discord_username,
                    )

                    # Ensure user is a member of the organization
                    member = await OrganizationMember.get_or_none(
                        organization_id=organization_id, user_id=user.id
                    )
                    if not member:
                        await OrganizationMember.create(
                            organization_id=organization_id, user_id=user.id
                        )
                        logger.info(
                            "Added crew user %s to organization %s",
                            user.id,
                            organization_id,
                        )

                    return user

        # Try to find placeholder user by SpeedGaming ID (might need to upgrade to full user)
        user = await User.get_or_none(is_placeholder=True, speedgaming_id=sg_crew.id)

        if user:
            # If we now have a Discord ID, check if a real user with that ID already exists
            if sg_crew.discord_id_int:
                # Check if there's already a real user with this Discord ID
                existing_real_user = await User.get_or_none(
                    discord_id=sg_crew.discord_id_int, is_placeholder=False
                )

                if existing_real_user:
                    # A real user with this Discord ID exists - use that instead
                    logger.info(
                        "Found existing real user %s with Discord ID %s for placeholder %s (SG crew %s)",
                        existing_real_user.id,
                        sg_crew.discord_id_int,
                        user.id,
                        sg_crew.id,
                    )

                    # TODO: In the future, we could merge the placeholder into the real user
                    # For now, we'll use the real user and leave the placeholder

                    # Ensure real user is a member of the organization
                    member = await OrganizationMember.get_or_none(
                        organization_id=organization_id, user_id=existing_real_user.id
                    )
                    if not member:
                        await OrganizationMember.create(
                            organization_id=organization_id,
                            user_id=existing_real_user.id,
                        )
                        logger.info(
                            "Added existing real user %s to organization %s",
                            existing_real_user.id,
                            organization_id,
                        )

                    return existing_real_user

                # No existing real user - upgrade the placeholder
                if not user.discord_id:
                    logger.info(
                        "Upgrading placeholder crew user %s to full user with Discord ID %s",
                        user.id,
                        sg_crew.discord_id_int,
                    )

                    # Best-effort username from discord_tag
                    discord_username = None
                    if sg_crew.discord_tag:
                        discord_username = (
                            sg_crew.discord_tag.split("#")[0]
                            if "#" in sg_crew.discord_tag
                            else sg_crew.discord_tag
                        )

                    if not discord_username:
                        # Fallback: use display name or streaming username
                        discord_username = (
                            sg_crew.public_stream
                            or sg_crew.display_name
                            or f"user_{sg_crew.discord_id_int}"
                        )

                    user.discord_id = sg_crew.discord_id_int
                    user.discord_username = discord_username
                    user.is_placeholder = False  # No longer a placeholder
                    await user.save()

                    logger.info(
                        "Upgraded crew user %s: discord_id=%s, username=%s",
                        user.id,
                        user.discord_id,
                        user.discord_username,
                    )
                    return user

            # Still a placeholder (no Discord ID provided), just update display name if needed
            logger.info(
                "Found existing placeholder crew user for SG crew %s", sg_crew.id
            )

            # Update display name if it has changed
            new_display_name = (
                sg_crew.public_stream or sg_crew.display_name or f"sg_crew_{sg_crew.id}"
            )

            if user.display_name != new_display_name:
                logger.info(
                    "Updating placeholder crew user %s display name: %s -> %s",
                    user.id,
                    user.display_name,
                    new_display_name,
                )
                user.display_name = new_display_name
                await user.save()

            return user

        # Create new user
        # If we have a Discord ID, create full user; otherwise create placeholder

        # Determine username
        if sg_crew.discord_id_int:
            # We have Discord ID - create full user with best-effort username
            discord_id = sg_crew.discord_id_int

            # Try to extract username from discord_tag
            if sg_crew.discord_tag:
                discord_username = (
                    sg_crew.discord_tag.split("#")[0]
                    if "#" in sg_crew.discord_tag
                    else sg_crew.discord_tag
                )
            else:
                # Best effort: use streaming name, display name, or generic fallback
                discord_username = (
                    sg_crew.public_stream
                    or sg_crew.display_name
                    or f"user_{discord_id}"
                )

            is_placeholder = False
            logger.info(
                "Creating full crew user with Discord ID %s (username: %s) for SpeedGaming crew '%s'",
                discord_id,
                discord_username,
                sg_crew.display_name,
            )
        else:
            # No Discord ID - create placeholder
            discord_id = None
            discord_username = f"sg_crew_{sg_crew.id}"
            is_placeholder = True
            logger.info(
                "Creating placeholder crew user for SpeedGaming crew '%s' (no Discord ID available)",
                sg_crew.display_name,
            )

        # Determine best display name
        # Priority: public_stream (Twitch), display_name
        display_name = sg_crew.public_stream or sg_crew.display_name or discord_username

        # Create user
        user = await User.create(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_discriminator=(
                "0000" if sg_crew.discord_tag and "#" in sg_crew.discord_tag else None
            ),
            discord_avatar=None,
            discord_email=None,
            display_name=display_name,
            is_placeholder=is_placeholder,
            speedgaming_id=sg_crew.id,  # Store SpeedGaming ID for tracking
        )

        user_type = "placeholder" if is_placeholder else "full"
        logger.info(
            "Created %s crew user %s for SpeedGaming crew '%s' "
            "(SG ID: %s, discord_id: %s, display_name: %s)",
            user_type,
            user.id,
            sg_crew.display_name,
            sg_crew.id,
            discord_id,
            display_name,
        )

        # Add to organization
        await OrganizationMember.create(
            organization_id=organization_id, user_id=user.id
        )
        logger.info("Added crew user %s to organization %s", user.id, organization_id)

        return user

    async def _find_or_create_stream_channel(
        self,
        organization_id: int,
        sg_channel: SpeedGamingChannel,
    ) -> Optional[StreamChannel]:
        """
        Find existing stream channel by name or create new one.

        Matches by channel name within the organization.
        Creates a new channel if no match is found.

        Args:
            organization_id: Organization ID
            sg_channel: SpeedGaming channel data

        Returns:
            StreamChannel object (existing or newly created)
        """
        # Try to find existing channel by name
        channel = await self.stream_channel_repo.get_by_name(
            organization_id=organization_id, name=sg_channel.name
        )

        if channel:
            logger.info(
                "Matched SpeedGaming channel '%s' to existing stream channel %s",
                sg_channel.name,
                channel.id,
            )
            return channel

        # Create new stream channel
        # Use SpeedGaming slug as the stream URL base (if we want to construct it)
        # For now, we'll leave stream_url empty since SpeedGaming doesn't provide it
        channel = await self.stream_channel_repo.create(
            organization_id=organization_id,
            name=sg_channel.name,
            stream_url=None,  # SpeedGaming API doesn't provide stream URLs
            is_active=True,
        )
        logger.info(
            "Created stream channel %s for SpeedGaming channel '%s' (ID: %s)",
            channel.id,
            sg_channel.name,
            sg_channel.id,
        )

        return channel

    async def _sync_match_players(
        self, match: Match, sg_players: List[SpeedGamingPlayer], organization_id: int
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
        current_players = (
            await MatchPlayers.filter(match=match).prefetch_related("user").all()
        )

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
        new_discord_ids = {p.discord_id_int for p in sg_players if p.discord_id_int}

        # Find players to add (in SG but not in current)
        for sg_player in sg_players:
            # Check if this player is already in the match
            already_exists = False

            # Check by Discord ID first
            if sg_player.discord_id_int:
                for mp in current_players:
                    if (
                        not mp.user.is_placeholder
                        and mp.user.discord_id == sg_player.discord_id_int
                    ):
                        already_exists = True
                        break

            # Check by SpeedGaming ID for placeholders
            if not already_exists and sg_player.id in current_sg_ids:
                already_exists = True

            if not already_exists:
                # Add new player
                user = await self._find_or_create_user(organization_id, sg_player)

                # Register player with tournament (if not already registered)
                # Skip RaceTime account requirement - register all players
                await match.fetch_related("tournament")
                await self.tournament_repo.register_user_for_tournament(
                    organization_id=organization_id,
                    tournament_id=match.tournament_id,
                    user_id=user.id,
                )
                logger.info(
                    "Registered player %s with tournament %s",
                    user.id,
                    match.tournament_id,
                )

                await MatchPlayers.create(match=match, user=user)
                logger.info(
                    "Added new player %s to match %s (SG player %s)",
                    user.id,
                    match.id,
                    sg_player.id,
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
                    match.id,
                )
                await mp.delete()

    async def _sync_match_crew(
        self,
        match: Match,
        sg_commentators: List[SpeedGamingCrewMember],
        sg_trackers: List[SpeedGamingCrewMember],
        organization_id: int,
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
        current_crew = await Crew.filter(match=match).prefetch_related("user").all()

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
                    if (
                        crew.role == CrewRole.COMMENTATOR
                        and not crew.user.is_placeholder
                        and crew.user.discord_id == sg_comm.discord_id_int
                    ):
                        already_exists = True
                        break

            if not already_exists and sg_comm.id in current_commentator_sg_ids:
                already_exists = True

            if not already_exists:
                user = await self._find_or_create_crew_user(organization_id, sg_comm)
                await Crew.create(
                    match=match, user=user, role=CrewRole.COMMENTATOR, approved=True
                )
                logger.info(
                    "Added new commentator %s to match %s (SG crew %s)",
                    user.id,
                    match.id,
                    sg_comm.id,
                )

        # Sync trackers (approved only)
        approved_trackers = [t for t in sg_trackers if t.approved]
        for sg_tracker in approved_trackers:
            # Check if already exists
            already_exists = False

            if sg_tracker.discord_id_int:
                for crew in current_crew:
                    if (
                        crew.role == CrewRole.TRACKER
                        and not crew.user.is_placeholder
                        and crew.user.discord_id == sg_tracker.discord_id_int
                    ):
                        already_exists = True
                        break

            if not already_exists and sg_tracker.id in current_tracker_sg_ids:
                already_exists = True

            if not already_exists:
                user = await self._find_or_create_crew_user(organization_id, sg_tracker)
                await Crew.create(
                    match=match, user=user, role=CrewRole.TRACKER, approved=True
                )
                logger.info(
                    "Added new tracker %s to match %s (SG crew %s)",
                    user.id,
                    match.id,
                    sg_tracker.id,
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
                    match.id,
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
        existing_match = await Match.get_or_none(speedgaming_episode_id=episode.id)

        # If match is already finished, skip it (don't touch completed matches)
        if existing_match and existing_match.finished_at is not None:
            logger.debug(
                "Match %s (episode %s) is already finished, skipping update",
                existing_match.id,
                episode.id,
            )
            return existing_match

        # Get organization ID from tournament
        await tournament.fetch_related("organization")
        organization_id = tournament.organization_id

        # Check if match should be auto-finished (more than 4 hours in the past)
        # Only auto-finish if no manual status has been set
        current_time = datetime.now(timezone.utc)
        if existing_match and existing_match.scheduled_at:
            # Check if any manual status has been set
            has_manual_status = bool(
                existing_match.checked_in_at
                or existing_match.started_at
                or existing_match.finished_at
                or existing_match.confirmed_at
            )

            if not has_manual_status:
                time_since_scheduled = current_time - existing_match.scheduled_at
                # 4 hours = 14400 seconds
                if time_since_scheduled.total_seconds() > 14400:
                    logger.info(
                        "Match %s (episode %s) is more than 4 hours past scheduled time, auto-finishing",
                        existing_match.id,
                        episode.id,
                    )
                    existing_match.finished_at = current_time
                    await existing_match.save()
                    return existing_match
            else:
                logger.debug(
                    "Match %s (episode %s) has manual status set, skipping auto-finish",
                    existing_match.id,
                    episode.id,
                )

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

        # Find or create stream channel (if episode has channels)
        stream_channel = None
        if episode.channels:
            # Use the first channel (SpeedGaming episodes typically have one primary channel)
            sg_channel = episode.channels[0]
            stream_channel = await self._find_or_create_stream_channel(
                organization_id=organization_id, sg_channel=sg_channel
            )

        if existing_match:
            # Update existing match
            logger.info(
                "Episode %s already exists as match %s, checking for updates",
                episode.id,
                existing_match.id,
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
                    episode.when,
                )

            if existing_match.title != match_title:
                existing_match.title = match_title
                needs_update = True
                logger.info(
                    "Episode %s title changed: %s -> %s",
                    episode.id,
                    existing_match.title,
                    match_title,
                )

            # Check if stream channel changed
            new_stream_channel_id = stream_channel.id if stream_channel else None
            if existing_match.stream_channel_id != new_stream_channel_id:
                existing_match.stream_channel_id = new_stream_channel_id
                needs_update = True
                logger.info(
                    "Episode %s stream channel changed: %s -> %s",
                    episode.id,
                    existing_match.stream_channel_id,
                    new_stream_channel_id,
                )

            if needs_update:
                await existing_match.save()
                logger.info(
                    "Updated match %s for episode %s", existing_match.id, episode.id
                )

            # Check for player changes
            await self._sync_match_players(existing_match, all_players, organization_id)

            # Check for crew changes
            await self._sync_match_crew(
                existing_match, episode.commentators, episode.trackers, organization_id
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
            stream_channel=stream_channel,  # Assign stream channel
        )
        logger.info("Created match %s for episode %s", match.id, episode.id)

        # Add players
        for sg_player in all_players:
            user = await self._find_or_create_user(organization_id, sg_player)

            # Register player with tournament (if not already registered)
            # Skip RaceTime account requirement - register all players
            await self.tournament_repo.register_user_for_tournament(
                organization_id=organization_id,
                tournament_id=tournament.id,
                user_id=user.id,
            )
            logger.info(
                "Registered player %s with tournament %s", user.id, tournament.id
            )

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
                    match.id,
                )
                continue

            user = await self._find_or_create_crew_user(organization_id, sg_commentator)

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
                    match.id,
                )
                continue

            user = await self._find_or_create_crew_user(organization_id, sg_tracker)

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
            "%s commentators, %s trackers%s",
            episode.id,
            match.id,
            len(all_players),
            approved_commentators,
            approved_trackers,
            f", stream channel: {stream_channel.name}" if stream_channel else "",
        )

        return match

    async def import_episodes_for_tournament(
        self, tournament_id: int
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
                start_time=start_time,
            )
            return (0, 0, 0)

        if not tournament.speedgaming_enabled:
            logger.info(
                "SpeedGaming integration disabled for tournament %s", tournament_id
            )
            return (0, 0, 0)

        if not tournament.speedgaming_event_slug:
            logger.warning(
                "Tournament %s has no SpeedGaming event slug configured", tournament_id
            )
            await self._log_sync_result(
                tournament_id,
                tournament.organization_id,
                success=False,
                error="No event slug configured",
                start_time=start_time,
            )
            return (0, 0, 0)

        # Fetch episodes from SpeedGaming
        try:
            episodes = await self.sg_service.get_upcoming_episodes_by_event(
                tournament.speedgaming_event_slug
            )
        except Exception as e:
            logger.error(
                "Failed to fetch episodes for tournament %s: %s", tournament_id, e
            )
            await self._log_sync_result(
                tournament_id,
                tournament.organization_id,
                success=False,
                error=f"API error: {str(e)}",
                start_time=start_time,
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
                existing = await Match.get_or_none(speedgaming_episode_id=episode.id)

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
        deleted_count = await self._detect_deleted_episodes(tournament, sg_episode_ids)

        logger.info(
            "Completed import for tournament %s: %s imported, "
            "%s updated, %s deleted",
            tournament_id,
            imported_count,
            updated_count,
            deleted_count,
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
            start_time=start_time,
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
        start_time: Optional[datetime] = None,
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
            },
        )

    async def _log_aggregated_sync_result(
        self,
        success: bool,
        imported: int = 0,
        updated: int = 0,
        deleted: int = 0,
        error: Optional[str] = None,
        start_time: Optional[datetime] = None,
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
            },
        )

    async def _detect_deleted_episodes(
        self, tournament: Tournament, current_episode_ids: set[int]
    ) -> int:
        """
        Detect and delete matches for episodes no longer in SpeedGaming.

        Also auto-finishes matches that are more than 4 hours past their scheduled time
        before deletion to preserve match data.

        Args:
            tournament: Tournament to check
            current_episode_ids: Set of episode IDs currently in SpeedGaming

        Returns:
            Number of matches deleted
        """
        # Find all matches for this tournament that came from SpeedGaming
        existing_matches = await Match.filter(
            tournament=tournament, speedgaming_episode_id__isnull=False
        ).all()

        if not existing_matches:
            return 0

        deleted_count = 0
        current_time = datetime.now(timezone.utc)
        four_hours_ago = current_time - timedelta(hours=4)

        # Batch collect matches that need auto-finishing
        matches_to_finish = []
        matches_to_check_deletion = []

        for match in existing_matches:
            # Check if match should be auto-finished (more than 4 hours past scheduled time)
            # Do NOT auto-finish if match has a RaceTime room linked
            if (
                match.scheduled_at
                and not match.finished_at
                and match.scheduled_at < four_hours_ago
            ):

                # Check if match has a RaceTime room
                has_racetime_room = await RacetimeRoom.exists(match_id=match.id)

                if has_racetime_room:
                    logger.info(
                        "Match %s (episode %s) has RaceTime room linked, skipping auto-finish",
                        match.id,
                        match.speedgaming_episode_id,
                    )
                else:
                    match.finished_at = current_time
                    matches_to_finish.append(match)
                    logger.info(
                        "Match %s (episode %s) is more than 4 hours past scheduled time, marking for auto-finish",
                        match.id,
                        match.speedgaming_episode_id,
                    )

            # If episode ID is not in current list and match is not finished, check for deletion
            if (
                match.speedgaming_episode_id not in current_episode_ids
                and not match.finished_at
            ):
                matches_to_check_deletion.append(match)

        # Batch save all auto-finished matches
        if matches_to_finish:
            for match in matches_to_finish:
                await match.save()
            logger.info(
                "Auto-finished %s matches that were >4 hours past scheduled time",
                len(matches_to_finish),
            )

        # Check deletion for unfinished matches not in current schedule
        for match in matches_to_check_deletion:
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
                        match.id,
                    )
                    await match.delete()
                    deleted_count += 1
                else:
                    logger.info(
                        "Episode %s still exists but not in event schedule, "
                        "keeping match %s",
                        match.speedgaming_episode_id,
                        match.id,
                    )

            except Exception as e:
                logger.error(
                    "Error checking episode %s: %s", match.speedgaming_episode_id, e
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
            speedgaming_enabled=True, is_active=True
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
                    "Error importing episodes for tournament %s: %s", tournament.id, e
                )
                errors.append(f"Tournament {tournament.id}: {str(e)}")

        logger.info(
            "Completed import for all tournaments: %s imported, "
            "%s updated, %s deleted",
            total_imported,
            total_updated,
            total_deleted,
        )

        # Log aggregated sync result
        await self._log_aggregated_sync_result(
            success=len(errors) == 0,
            imported=total_imported,
            updated=total_updated,
            deleted=total_deleted,
            error="; ".join(errors) if errors else None,
            start_time=start_time,
        )

        return (total_imported, total_updated, total_deleted)
