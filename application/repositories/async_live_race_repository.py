"""
Async Live Race Repository.

Data access layer for async tournament live races.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional
from models import AsyncTournamentLiveRace, AsyncTournamentRace, User

logger = logging.getLogger(__name__)


class AsyncLiveRaceRepository:
    """Repository for async tournament live race data access."""

    async def create_live_race(
        self,
        tournament_id: int,
        pool_id: int,
        scheduled_at: Optional[datetime] = None,
        match_title: Optional[str] = None,
        episode_id: Optional[int] = None,
        permalink_id: Optional[int] = None,
        race_room_profile_id: Optional[int] = None,
        racetime_goal: Optional[str] = None,
    ) -> AsyncTournamentLiveRace:
        """
        Create a new live race.

        Args:
            tournament_id: Tournament ID
            pool_id: Pool ID
            scheduled_at: When race is scheduled to start
            match_title: Display name for race
            episode_id: SpeedGaming episode ID (optional)
            permalink_id: Specific permalink (optional, auto-selected if not provided)
            race_room_profile_id: Race room profile (optional, uses tournament default if not provided)
            racetime_goal: RaceTime.gg goal text

        Returns:
            Created live race
        """
        live_race = await AsyncTournamentLiveRace.create(
            tournament_id=tournament_id,
            pool_id=pool_id,
            scheduled_at=scheduled_at,
            match_title=match_title,
            episode_id=episode_id,
            permalink_id=permalink_id,
            race_room_profile_id=race_room_profile_id,
            racetime_goal=racetime_goal,
            status='scheduled',
        )
        logger.info("Created live race %s for tournament %s", live_race.id, tournament_id)
        return live_race

    async def get_by_id(self, live_race_id: int) -> Optional[AsyncTournamentLiveRace]:
        """
        Get live race by ID.

        Args:
            live_race_id: Live race ID

        Returns:
            Live race if found, None otherwise
        """
        return await AsyncTournamentLiveRace.filter(id=live_race_id).first()

    async def get_by_id_with_relations(
        self, live_race_id: int
    ) -> Optional[AsyncTournamentLiveRace]:
        """
        Get live race by ID with related data.

        Args:
            live_race_id: Live race ID

        Returns:
            Live race with tournament, pool, permalink if found, None otherwise
        """
        return await AsyncTournamentLiveRace.filter(id=live_race_id).prefetch_related(
            'tournament',
            'pool',
            'permalink',
            'race_room_profile',
        ).first()

    async def get_by_episode_id(self, episode_id: int) -> Optional[AsyncTournamentLiveRace]:
        """
        Get live race by SpeedGaming episode ID.

        Args:
            episode_id: Episode ID

        Returns:
            Live race if found, None otherwise
        """
        return await AsyncTournamentLiveRace.filter(episode_id=episode_id).first()

    async def get_by_racetime_slug(
        self, racetime_slug: str
    ) -> Optional[AsyncTournamentLiveRace]:
        """
        Get live race by RaceTime.gg slug.

        Args:
            racetime_slug: RaceTime slug (e.g., "alttpr/cool-icerod-1234")

        Returns:
            Live race if found, None otherwise
        """
        return await AsyncTournamentLiveRace.filter(racetime_slug=racetime_slug).first()

    async def update_live_race(
        self,
        live_race_id: int,
        **updates
    ) -> AsyncTournamentLiveRace:
        """
        Update live race fields.

        Args:
            live_race_id: Live race ID
            **updates: Fields to update

        Returns:
            Updated live race
        """
        live_race = await self.get_by_id(live_race_id)
        if not live_race:
            raise ValueError(f"Live race {live_race_id} not found")

        # Update fields
        for key, value in updates.items():
            if hasattr(live_race, key):
                setattr(live_race, key, value)

        await live_race.save()
        logger.info("Updated live race %s: %s", live_race_id, updates.keys())
        return live_race

    async def delete_live_race(self, live_race_id: int) -> None:
        """
        Delete a live race.

        Args:
            live_race_id: Live race ID
        """
        live_race = await self.get_by_id(live_race_id)
        if live_race:
            await live_race.delete()
            logger.info("Deleted live race %s", live_race_id)

    async def list_scheduled_races(
        self,
        tournament_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        upcoming_only: bool = True,
    ) -> list[AsyncTournamentLiveRace]:
        """
        Get upcoming scheduled races.

        Args:
            tournament_id: Filter by tournament (optional)
            organization_id: Filter by organization (optional)
            upcoming_only: Only return races scheduled in the future

        Returns:
            List of upcoming live races
        """
        query = AsyncTournamentLiveRace.filter(status='scheduled')

        if tournament_id:
            query = query.filter(tournament_id=tournament_id)

        if organization_id:
            query = query.filter(tournament__organization_id=organization_id)

        if upcoming_only:
            now = datetime.now(timezone.utc)
            query = query.filter(scheduled_at__gte=now)

        return await query.prefetch_related(
            'tournament',
            'pool',
            'permalink',
        ).order_by('scheduled_at')

    async def list_races_for_tournament(
        self,
        tournament_id: int,
        status: Optional[str] = None,
    ) -> list[AsyncTournamentLiveRace]:
        """
        Get all live races for a tournament.

        Args:
            tournament_id: Tournament ID
            status: Filter by status (optional)

        Returns:
            List of live races
        """
        query = AsyncTournamentLiveRace.filter(tournament_id=tournament_id)

        if status:
            query = query.filter(status=status)

        return await query.prefetch_related(
            'pool',
            'permalink',
        ).order_by('-created_at')

    async def get_eligible_participants(
        self,
        live_race_id: int,
    ) -> list[tuple[User, bool, Optional[str]]]:
        """
        Get players eligible for a live race.

        Returns list of tuples: (user, is_eligible, reason_if_not_eligible)

        Args:
            live_race_id: Live race ID

        Returns:
            List of (User, is_eligible, reason) tuples
        """
        live_race = await self.get_by_id_with_relations(live_race_id)
        if not live_race:
            return []

        # Get all organization members
        await live_race.fetch_related('tournament__organization__members__user')
        members = live_race.tournament.organization.members

        eligible_users = []

        for member in members:
            user = member.user
            is_eligible = True
            reason = None

            # Check if user has exceeded runs_per_pool limit
            pool_race_count = await AsyncTournamentRace.filter(
                tournament_id=live_race.tournament_id,
                permalink__pool_id=live_race.pool_id,
                user_id=user.id,
                status__in=['finished', 'in_progress'],
            ).count()

            if pool_race_count >= live_race.tournament.runs_per_pool:
                is_eligible = False
                reason = f"Already completed {pool_race_count} race(s) in this pool (limit: {live_race.tournament.runs_per_pool})"

            # Check if user has active pending/in_progress races
            active_race_count = await AsyncTournamentRace.filter(
                tournament_id=live_race.tournament_id,
                user_id=user.id,
                status__in=['pending', 'in_progress'],
            ).count()

            if active_race_count > 0 and is_eligible:
                is_eligible = False
                reason = "Has active race in progress"

            eligible_users.append((user, is_eligible, reason))

        return eligible_users

    async def create_participant_races(
        self,
        live_race_id: int,
        user_ids: list[int],
    ) -> list[AsyncTournamentRace]:
        """
        Create race records for live race participants.

        Called when race starts to create AsyncTournamentRace records
        for each participant who joined the RaceTime.gg room.

        Args:
            live_race_id: Live race ID
            user_ids: List of user IDs who joined

        Returns:
            List of created race records
        """
        live_race = await self.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError(f"Live race {live_race_id} not found")

        races = []
        for user_id in user_ids:
            # Check if race already exists
            existing = await AsyncTournamentRace.filter(
                live_race_id=live_race_id,
                user_id=user_id,
            ).first()

            if existing:
                races.append(existing)
                continue

            # Create new race
            race = await AsyncTournamentRace.create(
                tournament_id=live_race.tournament_id,
                permalink_id=live_race.permalink_id,
                user_id=user_id,
                live_race_id=live_race_id,
                status='pending',
            )
            races.append(race)
            logger.info(
                "Created race %s for user %s in live race %s",
                race.id, user_id, live_race_id
            )

        return races
