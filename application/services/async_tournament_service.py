"""Service layer for Async Tournament management.

Contains org-scoped business logic, authorization checks, and scoring algorithms.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import cached_property
import logging
import asyncio

from models import User
from models.async_tournament import (
    AsyncTournament,
    AsyncTournamentPool,
    AsyncTournamentPermalink,
    AsyncTournamentRace,
)
from application.repositories.async_tournament_repository import AsyncTournamentRepository
from application.services.organization_service import OrganizationService

logger = logging.getLogger(__name__)

# Scoring constants from original SahasrahBot
QUALIFIER_MAX_SCORE = 105
QUALIFIER_MIN_SCORE = 0
MAX_POOL_IMBALANCE = 3

# Lock for score calculation to prevent concurrent calculations
score_calculation_lock = asyncio.Lock()


@dataclass
class LeaderboardEntry:
    """Represents a leaderboard entry for a user."""
    user: User
    races: List[Optional[AsyncTournamentRace]]

    @cached_property
    def score(self) -> float:
        """Average score of all races (including unfinished as 0)."""
        scores = [
            r.score if r is not None and r.score is not None else 0
            for r in self.races
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @cached_property
    def estimate(self) -> float:
        """Estimated score averaging only finished races."""
        scores = [
            r.score
            for r in self.races
            if r is not None and r.status == "finished" and r.score is not None
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @cached_property
    def finished_race_count(self) -> int:
        """Count of finished races."""
        return len([r for r in self.races if r is not None and r.status == "finished"])

    @cached_property
    def unattempted_race_count(self) -> int:
        """Count of unattempted races."""
        return len([r for r in self.races if r is None])

    @cached_property
    def forfeited_race_count(self) -> int:
        """Count of forfeited or disqualified races."""
        return len([r for r in self.races if r is not None and r.status in ["forfeit", "disqualified"]])


class AsyncTournamentService:
    """Business logic for async tournaments with organization scoping."""

    def __init__(self) -> None:
        self.repo = AsyncTournamentRepository()
        self.org_service = OrganizationService()

    async def can_manage_async_tournaments(self, user: Optional[User], organization_id: int) -> bool:
        """Check if user can manage async tournaments in the organization."""
        if not user:
            return False
        # Check for ADMIN or TOURNAMENT_ADMIN permission
        return await self.org_service.user_can_manage_tournaments(user, organization_id)

    # Tournament CRUD

    async def list_org_tournaments(
        self,
        user: Optional[User],
        organization_id: int
    ) -> List[AsyncTournament]:
        """List async tournaments for an organization after access check."""
        # Anyone in the org can view tournaments
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning("Unauthorized list_org_tournaments by user %s for org %s", getattr(user, 'id', None), organization_id)
            return []

        return await self.repo.list_by_org(organization_id)

    async def get_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int
    ) -> Optional[AsyncTournament]:
        """Get a tournament by ID if user has access."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning("Unauthorized get_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None

        return await self.repo.get_by_id(tournament_id, organization_id)

    async def create_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        discord_channel_id: Optional[int] = None,
        runs_per_pool: int = 1,
    ) -> Optional[AsyncTournament]:
        """Create a new async tournament."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning("Unauthorized create_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None

        tournament = await self.repo.create(
            organization_id=organization_id,
            name=name,
            description=description,
            is_active=is_active,
            discord_channel_id=discord_channel_id,
            runs_per_pool=runs_per_pool,
        )

        await self.repo.create_audit_log(
            tournament_id=tournament.id,
            action="create_tournament",
            details=f"Created tournament '{name}'",
            user_id=user.id if user else None,
        )

        return tournament

    async def update_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        **fields
    ) -> Optional[AsyncTournament]:
        """Update a tournament."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning("Unauthorized update_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None

        tournament = await self.repo.update(tournament_id, organization_id, **fields)
        if tournament:
            await self.repo.create_audit_log(
                tournament_id=tournament_id,
                action="update_tournament",
                details=f"Updated tournament with fields: {', '.join(fields.keys())}",
                user_id=user.id if user else None,
            )

        return tournament

    async def delete_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int
    ) -> bool:
        """Delete a tournament."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning("Unauthorized delete_tournament by user %s for org %s", getattr(user, 'id', None), organization_id)
            return False

        # Audit log before delete
        await self.repo.create_audit_log(
            tournament_id=tournament_id,
            action="delete_tournament",
            details=f"Deleted tournament {tournament_id}",
            user_id=user.id if user else None,
        )

        return await self.repo.delete(tournament_id, organization_id)

    # Pool management

    async def create_pool(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        name: str,
        description: Optional[str] = None,
    ) -> Optional[AsyncTournamentPool]:
        """Create a pool for a tournament."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning("Unauthorized create_pool by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None

        pool = await self.repo.create_pool(tournament_id, organization_id, name, description)
        if pool:
            await self.repo.create_audit_log(
                tournament_id=tournament_id,
                action="create_pool",
                details=f"Created pool '{name}'",
                user_id=user.id if user else None,
            )

        return pool

    # Permalink management

    async def create_permalink(
        self,
        user: Optional[User],
        organization_id: int,
        pool_id: int,
        url: str,
        notes: Optional[str] = None,
    ) -> Optional[AsyncTournamentPermalink]:
        """Create a permalink for a pool."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning("Unauthorized create_permalink by user %s for org %s", getattr(user, 'id', None), organization_id)
            return None

        permalink = await self.repo.create_permalink(pool_id, organization_id, url, notes)
        if permalink:
            pool = await AsyncTournamentPool.get(id=pool_id)
            await self.repo.create_audit_log(
                tournament_id=pool.tournament_id,
                action="create_permalink",
                details=f"Created permalink in pool '{pool.name}'",
                user_id=user.id if user else None,
            )

        return permalink

    # Race management

    async def get_user_races(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int
    ) -> List[AsyncTournamentRace]:
        """Get all races for a user in a tournament."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member or not user:
            return []

        return await self.repo.list_races(tournament_id, organization_id, user_id=user.id)

    async def create_race(
        self,
        user: User,
        organization_id: int,
        tournament_id: int,
        permalink_id: int,
        discord_thread_id: Optional[int] = None,
    ) -> Optional[AsyncTournamentRace]:
        """Create a new race for a user."""
        # User must be org member
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning("Unauthorized create_race by user %s for org %s", user.id, organization_id)
            return None

        race = await self.repo.create_race(
            tournament_id=tournament_id,
            organization_id=organization_id,
            permalink_id=permalink_id,
            user_id=user.id,
            discord_thread_id=discord_thread_id,
        )

        if race:
            await self.repo.create_audit_log(
                tournament_id=tournament_id,
                action="create_race",
                details=f"User {user.discord_username} created race {race.id}",
                user_id=user.id,
            )

        return race

    async def start_race(
        self,
        user: User,
        organization_id: int,
        race_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Mark a race as in progress."""
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race or race.user_id != user.id:
            logger.warning("Unauthorized start_race by user %s for race %s", user.id, race_id)
            return None

        if race.status != 'pending':
            logger.warning("Cannot start race %s with status %s", race_id, race.status)
            return None

        race = await self.repo.update_race(
            race_id,
            organization_id,
            status='in_progress',
            start_time=datetime.utcnow(),
        )

        if race:
            await self.repo.create_audit_log(
                tournament_id=race.tournament_id,
                action="start_race",
                details=f"Race {race_id} started",
                user_id=user.id,
            )

        return race

    async def finish_race(
        self,
        user: User,
        organization_id: int,
        race_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Mark a race as finished."""
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race or race.user_id != user.id:
            logger.warning("Unauthorized finish_race by user %s for race %s", user.id, race_id)
            return None

        if race.status != 'in_progress':
            logger.warning("Cannot finish race %s with status %s", race_id, race.status)
            return None

        race = await self.repo.update_race(
            race_id,
            organization_id,
            status='finished',
            end_time=datetime.utcnow(),
        )

        if race:
            await self.repo.create_audit_log(
                tournament_id=race.tournament_id,
                action="finish_race",
                details=f"Race {race_id} finished with time {race.elapsed_time_formatted}",
                user_id=user.id,
            )

            # Trigger score recalculation for the permalink
            await self.calculate_permalink_scores(race.permalink_id, organization_id)

        return race

    async def forfeit_race(
        self,
        user: User,
        organization_id: int,
        race_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Mark a race as forfeited."""
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race or race.user_id != user.id:
            logger.warning("Unauthorized forfeit_race by user %s for race %s", user.id, race_id)
            return None

        if race.status not in ['pending', 'in_progress']:
            logger.warning("Cannot forfeit race %s with status %s", race_id, race.status)
            return None

        race = await self.repo.update_race(
            race_id,
            organization_id,
            status='forfeit',
        )

        if race:
            await self.repo.create_audit_log(
                tournament_id=race.tournament_id,
                action="forfeit_race",
                details=f"Race {race_id} forfeited",
                user_id=user.id,
            )

        return race

    # Scoring logic

    async def calculate_permalink_scores(
        self,
        permalink_id: int,
        organization_id: int
    ) -> bool:
        """Calculate par time and scores for a permalink."""
        permalink = await AsyncTournamentPermalink.get_or_none(id=permalink_id).prefetch_related('pool__tournament')
        if not permalink or permalink.pool.tournament.organization_id != organization_id:
            return False

        # Get all finished races for this permalink (excluding reattempts)
        races = await AsyncTournamentRace.filter(
            permalink_id=permalink_id,
            status='finished',
            reattempted=False,
        )
        # Sort races by elapsed_time in Python, treating None as very large (so they go last)
        races = sorted(races, key=lambda r: r.elapsed_time or timedelta.max)

        if not races:
            logger.info("No finished races for permalink %s", permalink_id)
            return True

        # Calculate par time from top 5
        top_races = races[:5] if len(races) >= 5 else races
        par_times = [r.elapsed_time for r in top_races if r.elapsed_time]

        if not par_times:
            return True

        # Average of top times
        total_seconds = sum(t.total_seconds() for t in par_times)
        par_time_seconds = total_seconds / len(par_times)

        # Update permalink par time
        permalink.par_time = par_time_seconds
        permalink.par_updated_at = datetime.utcnow()
        await permalink.save()

        # Calculate scores for all finished races
        par_time_delta = timedelta(seconds=par_time_seconds)
        all_races = await AsyncTournamentRace.filter(
            permalink_id=permalink_id,
            status__in=['finished', 'forfeit', 'disqualified'],
            reattempted=False,
        )

        for race in all_races:
            if race.status == 'finished' and race.elapsed_time:
                score = self._calculate_qualifier_score(par_time_delta, race.elapsed_time)
            else:
                score = 0.0

            race.score = score
            race.score_updated_at = datetime.utcnow()
            await race.save(update_fields=['score', 'score_updated_at'])

        logger.info("Updated scores for permalink %s (par: %s)", permalink_id, par_time_delta)
        return True

    def _calculate_qualifier_score(self, par_time: timedelta, elapsed_time: timedelta) -> float:
        """Calculate qualifier score based on par time and elapsed time."""
        ratio = elapsed_time.total_seconds() / par_time.total_seconds()
        score = (2 - ratio) * 100
        return max(QUALIFIER_MIN_SCORE, min(QUALIFIER_MAX_SCORE, score))

    async def calculate_tournament_scores(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int
    ) -> bool:
        """Recalculate all scores for a tournament."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning("Unauthorized calculate_tournament_scores by user %s", getattr(user, 'id', None))
            return False

        async with score_calculation_lock:
            tournament = await self.repo.get_by_id(tournament_id, organization_id)
            if not tournament:
                return False

            await tournament.fetch_related('pools', 'pools__permalinks')

            for pool in tournament.pools:
                for permalink in pool.permalinks:
                    await self.calculate_permalink_scores(permalink.id, organization_id)

            logger.info("Recalculated all scores for tournament %s", tournament_id)
            return True

    async def get_leaderboard(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int
    ) -> List[LeaderboardEntry]:
        """Get leaderboard for a tournament."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning("Unauthorized get_leaderboard by user %s", getattr(user, 'id', None))
            return []

        async with score_calculation_lock:
            tournament = await self.repo.get_by_id(tournament_id, organization_id)
            if not tournament:
                return []

            await tournament.fetch_related('pools')

            # Get all user IDs who have participated
            all_races = await AsyncTournamentRace.filter(tournament_id=tournament_id).values('user_id')
            user_ids = list(set(r['user_id'] for r in all_races))

            leaderboard: List[LeaderboardEntry] = []

            for user_id in user_ids:
                races_list: List[Optional[AsyncTournamentRace]] = []

                # For each pool, get runs_per_pool races
                for pool in tournament.pools:
                    pool_races = await AsyncTournamentRace.filter(
                        user_id=user_id,
                        tournament_id=tournament_id,
                        permalink__pool_id=pool.id,
                        status__in=['finished', 'forfeit', 'disqualified'],
                        reattempted=False,
                    ).order_by('-score').limit(tournament.runs_per_pool)

                    for i in range(tournament.runs_per_pool):
                        try:
                            races_list.append(pool_races[i])
                        except IndexError:
                            races_list.append(None)

                participant_user = await User.get(id=user_id)
                entry = LeaderboardEntry(user=participant_user, races=races_list)
                leaderboard.append(entry)

            # Sort by score descending
            leaderboard.sort(key=lambda e: e.score, reverse=True)

            logger.info("Generated leaderboard for tournament %s with %s entries", tournament_id, len(leaderboard))
            return leaderboard
