"""Service layer for Async Tournament management.

Contains org-scoped business logic, authorization checks, and scoring algorithms.
"""

from __future__ import annotations
from typing import Optional, List, Tuple
from datetime import datetime, timedelta, timezone
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
from application.repositories.async_tournament_repository import (
    AsyncTournamentRepository,
)
from application.services.organizations.organization_service import OrganizationService
from application.services.authorization.authorization_service_v2 import (
    AuthorizationServiceV2,
)
from application.events import (
    EventBus,
    TournamentCreatedEvent,
    RaceSubmittedEvent,
    RaceApprovedEvent,
    RaceRejectedEvent,
)

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
            r.score if r is not None and r.score is not None else 0 for r in self.races
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
        return len(
            [
                r
                for r in self.races
                if r is not None and r.status in ["forfeit", "disqualified"]
            ]
        )


class AsyncTournamentService:
    """Business logic for async tournaments with organization scoping."""

    def __init__(self) -> None:
        self.repo = AsyncTournamentRepository()
        self.org_service: OrganizationService = OrganizationService()
        self.auth = AuthorizationServiceV2()

    async def can_manage_async_tournaments(
        self, user: Optional[User], organization_id: int
    ) -> bool:
        """Check if user can manage async tournaments in the organization."""
        if not user:
            return False

        # Use new authorization system
        return await self.auth.can(
            user,
            action=self.auth.get_action_for_operation("async_tournament", "manage"),
            resource=self.auth.get_resource_identifier("async_tournament", "*"),
            organization_id=organization_id,
        )

    async def can_review_async_races(
        self, user: Optional[User], organization_id: int
    ) -> bool:
        """
        Check if user can review async tournament races.

        Users with ASYNC_REVIEWER or ADMIN permissions can review races,
        and they can access all run information regardless of hide_results setting.
        """
        if not user:
            return False

        # Use new authorization system
        return await self.auth.can(
            user,
            action=self.auth.get_action_for_operation("async_race", "review"),
            resource=self.auth.get_resource_identifier("async_race", "*"),
            organization_id=organization_id,
        )

    # Tournament CRUD

    async def list_org_tournaments(
        self, user: Optional[User], organization_id: int
    ) -> List[AsyncTournament]:
        """List async tournaments for an organization after access check."""
        # Anyone in the org can view tournaments
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning(
                "Unauthorized list_org_tournaments by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return []

        return await self.repo.list_by_org(organization_id)

    async def list_active_org_tournaments(
        self, user: Optional[User], organization_id: int
    ) -> List[AsyncTournament]:
        """
        List active async tournaments for an organization.

        This method is accessible to all organization members.
        Used for displaying active tournaments in the UI.

        Args:
            user: Current user (must be a member of the organization)
            organization_id: Organization ID

        Returns:
            List of active tournaments, or empty list if user is not a member
        """
        # Anyone in the org can view active tournaments
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning(
                "Non-member user %s attempted to list active async tournaments for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return []

        return await self.repo.list_active_by_org(organization_id)

    async def get_tournament(
        self, user: Optional[User], organization_id: int, tournament_id: int
    ) -> Optional[AsyncTournament]:
        """Get a tournament by ID if user has access."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning(
                "Unauthorized get_tournament by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None

        return await self.repo.get_by_id(tournament_id, organization_id)

    async def create_tournament(
        self,
        user: Optional[User],
        organization_id: int,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        hide_results: bool = False,
        discord_channel_id: Optional[int] = None,
        runs_per_pool: int = 1,
        require_racetime_for_async_runs: bool = False,
    ) -> Tuple[Optional[AsyncTournament], List[str]]:
        """
        Create a new async tournament.

        Returns:
            Tuple of (tournament, warnings) where warnings contains any permission issues
        """
        warnings: List[str] = []

        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning(
                "Unauthorized create_tournament by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None, warnings

        # Check Discord channel permissions if a channel is specified
        if discord_channel_id:
            try:
                from application.services.discord.discord_guild_service import (
                    DiscordGuildService,
                )

                discord_service = DiscordGuildService()
                perm_check = (
                    await discord_service.check_async_tournament_channel_permissions(
                        discord_channel_id
                    )
                )

                if not perm_check.is_valid or perm_check.has_warnings:
                    warnings.extend(perm_check.warnings)
                    logger.warning(
                        "Channel %s has permission issues for tournament: %s",
                        discord_channel_id,
                        ", ".join(perm_check.warnings),
                    )
            except Exception as e:
                logger.error("Error checking channel permissions: %s", e, exc_info=True)
                warnings.append("Could not verify channel permissions")

        tournament = await self.repo.create(
            organization_id=organization_id,
            name=name,
            description=description,
            is_active=is_active,
            hide_results=hide_results,
            discord_channel_id=discord_channel_id,
            runs_per_pool=runs_per_pool,
            require_racetime_for_async_runs=require_racetime_for_async_runs,
        )

        # Cache permission warnings if channel was checked
        if discord_channel_id and warnings:
            tournament.discord_warnings = warnings
            tournament.discord_warnings_checked_at = datetime.now(timezone.utc)
            await tournament.save(
                update_fields=["discord_warnings", "discord_warnings_checked_at"]
            )

        await self.repo.create_audit_log(
            tournament_id=tournament.id,
            action="create_tournament",
            details=f"Created tournament '{name}'",
            user_id=user.id if user else None,
        )

        # Emit tournament created event
        event = TournamentCreatedEvent(
            entity_id=tournament.id,
            user_id=user.id if user else None,
            organization_id=organization_id,
            tournament_name=name,
            tournament_type="async",
        )
        await EventBus.emit(event)
        logger.debug("Emitted TournamentCreatedEvent for tournament %s", tournament.id)

        return tournament, warnings

    async def update_tournament(
        self, user: Optional[User], organization_id: int, tournament_id: int, **fields
    ) -> Tuple[Optional[AsyncTournament], List[str]]:
        """
        Update a tournament.

        Returns:
            Tuple of (tournament, warnings) where warnings contains any permission issues
        """
        warnings: List[str] = []

        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning(
                "Unauthorized update_tournament by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None, warnings

        # Get the current tournament to check if channel is changing
        current_tournament = await self.repo.get_by_id(tournament_id, organization_id)
        if not current_tournament:
            return None, warnings

        channel_changed = (
            "discord_channel_id" in fields
            and fields["discord_channel_id"] != current_tournament.discord_channel_id
        )

        # Check Discord channel permissions if channel is being updated
        if channel_changed and fields["discord_channel_id"]:
            try:
                from application.services.discord.discord_guild_service import (
                    DiscordGuildService,
                )

                discord_service = DiscordGuildService()
                perm_check = (
                    await discord_service.check_async_tournament_channel_permissions(
                        fields["discord_channel_id"]
                    )
                )

                if not perm_check.is_valid or perm_check.has_warnings:
                    warnings.extend(perm_check.warnings)
                    logger.warning(
                        "Channel %s has permission issues for tournament: %s",
                        fields["discord_channel_id"],
                        ", ".join(perm_check.warnings),
                    )

                # Cache the warnings
                fields["discord_warnings"] = perm_check.warnings
                fields["discord_warnings_checked_at"] = datetime.now(timezone.utc)

            except Exception as e:
                logger.error("Error checking channel permissions: %s", e, exc_info=True)
                warnings.append("Could not verify channel permissions")
                # Invalidate cache on error
                fields["discord_warnings"] = None
                fields["discord_warnings_checked_at"] = None
        elif channel_changed:
            # Channel was removed or changed to None, clear cache
            fields["discord_warnings"] = None
            fields["discord_warnings_checked_at"] = None

        tournament = await self.repo.update(tournament_id, organization_id, **fields)
        if tournament:
            await self.repo.create_audit_log(
                tournament_id=tournament_id,
                action="update_tournament",
                details=f"Updated tournament with fields: {', '.join(fields.keys())}",
                user_id=user.id if user else None,
            )

        return tournament, warnings

    async def delete_tournament(
        self, user: Optional[User], organization_id: int, tournament_id: int
    ) -> bool:
        """Delete a tournament."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning(
                "Unauthorized delete_tournament by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
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
            logger.warning(
                "Unauthorized create_pool by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None

        pool = await self.repo.create_pool(
            tournament_id, organization_id, name, description
        )
        if pool:
            await self.repo.create_audit_log(
                tournament_id=tournament_id,
                action="create_pool",
                details=f"Created pool '{name}'",
                user_id=user.id if user else None,
            )

        return pool

    async def update_pool(
        self, user: Optional[User], organization_id: int, pool_id: int, **fields
    ) -> Optional[AsyncTournamentPool]:
        """Update a pool."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning(
                "Unauthorized update_pool by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None

        pool = await self.repo.update_pool(pool_id, organization_id, **fields)
        if pool:
            await self.repo.create_audit_log(
                tournament_id=pool.tournament_id,
                action="update_pool",
                details=f"Updated pool '{pool.name}'",
                user_id=user.id if user else None,
            )

        return pool

    async def delete_pool(
        self, user: Optional[User], organization_id: int, pool_id: int
    ) -> bool:
        """Delete a pool and all associated data."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning(
                "Unauthorized delete_pool by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return False

        # Get pool details for audit log before deletion
        pool = await self.repo.get_pool_by_id(pool_id, organization_id)
        if not pool:
            return False

        tournament_id = pool.tournament_id
        pool_name = pool.name

        success = await self.repo.delete_pool(pool_id, organization_id)
        if success:
            await self.repo.create_audit_log(
                tournament_id=tournament_id,
                action="delete_pool",
                details=f"Deleted pool '{pool_name}'",
                user_id=user.id if user else None,
            )

        return success

    async def get_pool(
        self, user: Optional[User], organization_id: int, pool_id: int
    ) -> Optional[AsyncTournamentPool]:
        """Get a pool by ID with permission check."""
        if not await self.org_service.is_member(user, organization_id):
            logger.warning(
                "Unauthorized get_pool by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None

        return await self.repo.get_pool_by_id(pool_id, organization_id)

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
            logger.warning(
                "Unauthorized create_permalink by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None

        permalink = await self.repo.create_permalink(
            pool_id, organization_id, url, notes
        )
        if permalink:
            pool = await AsyncTournamentPool.get(id=pool_id)
            await self.repo.create_audit_log(
                tournament_id=pool.tournament_id,
                action="create_permalink",
                details=f"Created permalink in pool '{pool.name}'",
                user_id=user.id if user else None,
            )

        return permalink

    async def update_permalink(
        self, user: Optional[User], organization_id: int, permalink_id: int, **fields
    ) -> Optional[AsyncTournamentPermalink]:
        """Update a permalink."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning(
                "Unauthorized update_permalink by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return None

        permalink = await self.repo.update_permalink(
            permalink_id, organization_id, **fields
        )
        if permalink:
            pool = await AsyncTournamentPool.get(id=permalink.pool_id)
            await self.repo.create_audit_log(
                tournament_id=pool.tournament_id,
                action="update_permalink",
                details=f"Updated permalink in pool '{pool.name}'",
                user_id=user.id if user else None,
            )

        return permalink

    async def delete_permalink(
        self, user: Optional[User], organization_id: int, permalink_id: int
    ) -> bool:
        """Delete a permalink and all associated races."""
        if not await self.can_manage_async_tournaments(user, organization_id):
            logger.warning(
                "Unauthorized delete_permalink by user %s for org %s",
                getattr(user, "id", None),
                organization_id,
            )
            return False

        # Get permalink details for audit log before deletion
        permalink = await self.repo.get_permalink_by_id(permalink_id, organization_id)
        if not permalink:
            return False

        pool = await AsyncTournamentPool.get(id=permalink.pool_id)
        tournament_id = pool.tournament_id

        success = await self.repo.delete_permalink(permalink_id, organization_id)
        if success:
            await self.repo.create_audit_log(
                tournament_id=tournament_id,
                action="delete_permalink",
                details=f"Deleted permalink from pool '{pool.name}'",
                user_id=user.id if user else None,
            )

        return success

    # Race management

    async def get_user_races(
        self, user: Optional[User], organization_id: int, tournament_id: int
    ) -> List[AsyncTournamentRace]:
        """Get all races for a user in a tournament."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member or not user:
            return []

        return await self.repo.list_races(
            tournament_id, organization_id, user_id=user.id
        )

    async def get_permalink(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        permalink_id: int,
    ) -> Optional[AsyncTournamentPermalink]:
        """Get a permalink by ID."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member or not user:
            return None

        # Verify permalink belongs to this tournament
        permalink = await AsyncTournamentPermalink.get_or_none(id=permalink_id)
        if not permalink:
            return None

        await permalink.fetch_related("pool", "pool__tournament")
        if permalink.pool.tournament.id != tournament_id:
            return None
        if permalink.pool.tournament.organization_id != organization_id:
            return None

        return permalink

    async def get_permalink_races(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        permalink_id: int,
    ) -> List[AsyncTournamentRace]:
        """Get all races for a specific permalink."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member or not user:
            return []

        # Verify permalink belongs to this tournament
        permalink = await self.get_permalink(
            user, organization_id, tournament_id, permalink_id
        )
        if not permalink:
            return []

        return (
            await AsyncTournamentRace.filter(
                permalink_id=permalink_id, tournament_id=tournament_id
            )
            .prefetch_related("user")
            .all()
        )

    async def get_active_races_for_user(
        self, user: User, organization_id: int, tournament_id: int
    ) -> List[AsyncTournamentRace]:
        """Get active (pending or in-progress) races for a user in a tournament."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            return []

        return await AsyncTournamentRace.filter(
            user_id=user.id,
            tournament_id=tournament_id,
            status__in=["pending", "in_progress"],
        ).all()

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
            logger.warning(
                "Unauthorized create_race by user %s for org %s",
                user.id,
                organization_id,
            )
            return None

        # Check if user already has an in-progress race
        has_in_progress = await self.repo.has_in_progress_race(user.id, tournament_id)
        if has_in_progress:
            logger.warning(
                "User %s attempted to create race while having in-progress race in tournament %s",
                user.id,
                tournament_id,
            )
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
        self, user: User, organization_id: int, race_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Mark a race as in progress."""
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race or race.user_id != user.id:
            logger.warning(
                "Unauthorized start_race by user %s for race %s", user.id, race_id
            )
            return None

        if race.status != "pending":
            logger.warning("Cannot start race %s with status %s", race_id, race.status)
            return None

        race = await self.repo.update_race(
            race_id,
            organization_id,
            status="in_progress",
            start_time=datetime.now(timezone.utc),
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
        self, user: User, organization_id: int, race_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Mark a race as finished."""
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race or race.user_id != user.id:
            logger.warning(
                "Unauthorized finish_race by user %s for race %s", user.id, race_id
            )
            return None

        if race.status != "in_progress":
            logger.warning("Cannot finish race %s with status %s", race_id, race.status)
            return None

        race = await self.repo.update_race(
            race_id,
            organization_id,
            status="finished",
            end_time=datetime.now(timezone.utc),
        )

        if race:
            await self.repo.create_audit_log(
                tournament_id=race.tournament_id,
                action="finish_race",
                details=f"Race {race_id} finished with time {race.elapsed_time_formatted}",
                user_id=user.id,
            )

            # Emit race submitted event
            event = RaceSubmittedEvent(
                entity_id=race.id,
                user_id=user.id,
                organization_id=organization_id,
                tournament_id=race.tournament_id,
                permalink_id=race.permalink_id,
                racer_user_id=user.id,
                time_seconds=(
                    int(race.elapsed_time.total_seconds())
                    if race.elapsed_time
                    else None
                ),
            )
            await EventBus.emit(event)
            logger.debug("Emitted RaceSubmittedEvent for race %s", race.id)

            # Trigger score recalculation for the permalink
            await self.calculate_permalink_scores(race.permalink_id, organization_id)

        return race

    async def forfeit_race(
        self, user: User, organization_id: int, race_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Mark a race as forfeited."""
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race or race.user_id != user.id:
            logger.warning(
                "Unauthorized forfeit_race by user %s for race %s", user.id, race_id
            )
            return None

        if race.status not in ["pending", "in_progress"]:
            logger.warning(
                "Cannot forfeit race %s with status %s", race_id, race.status
            )
            return None

        race = await self.repo.update_race(
            race_id,
            organization_id,
            status="forfeit",
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
        self, permalink_id: int, organization_id: int
    ) -> bool:
        """Calculate par time and scores for a permalink."""
        permalink = await AsyncTournamentPermalink.get_or_none(
            id=permalink_id
        ).prefetch_related("pool__tournament")
        if (
            not permalink
            or permalink.pool.tournament.organization_id != organization_id
        ):
            return False

        # Get all finished races for this permalink (excluding reattempts)
        races = await AsyncTournamentRace.filter(
            permalink_id=permalink_id,
            status="finished",
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
        permalink.par_updated_at = datetime.now(timezone.utc)
        await permalink.save()

        # Calculate scores for all finished races
        par_time_delta = timedelta(seconds=par_time_seconds)
        all_races = await AsyncTournamentRace.filter(
            permalink_id=permalink_id,
            status__in=["finished", "forfeit", "disqualified"],
            reattempted=False,
        )

        for race in all_races:
            if race.status == "finished" and race.elapsed_time:
                score = self._calculate_qualifier_score(
                    par_time_delta, race.elapsed_time
                )
            else:
                score = 0.0

            race.score = score
            race.score_updated_at = datetime.now(timezone.utc)
            await race.save(update_fields=["score", "score_updated_at"])

        logger.info(
            "Updated scores for permalink %s (par: %s)", permalink_id, par_time_delta
        )
        return True

    def _calculate_qualifier_score(
        self, par_time: timedelta, elapsed_time: timedelta
    ) -> float:
        """Calculate qualifier score based on par time and elapsed time."""
        ratio = elapsed_time.total_seconds() / par_time.total_seconds()
        score = (2 - ratio) * 100
        return max(QUALIFIER_MIN_SCORE, min(QUALIFIER_MAX_SCORE, score))

    async def calculate_tournament_scores(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        system_task: bool = False,
    ) -> bool:
        """Recalculate all scores for a tournament."""
        # Allow system tasks to bypass authorization
        if not system_task and not await self.can_manage_async_tournaments(
            user, organization_id
        ):
            logger.warning(
                "Unauthorized calculate_tournament_scores by user %s",
                getattr(user, "id", None),
            )
            return False

        async with score_calculation_lock:
            tournament = await self.repo.get_by_id(tournament_id, organization_id)
            if not tournament:
                return False

            await tournament.fetch_related("pools", "pools__permalinks")

            for pool in tournament.pools:
                for permalink in pool.permalinks:
                    await self.calculate_permalink_scores(permalink.id, organization_id)

            logger.info("Recalculated all scores for tournament %s", tournament_id)
            return True

    async def get_leaderboard(
        self, user: Optional[User], organization_id: int, tournament_id: int
    ) -> List[LeaderboardEntry]:
        """Get leaderboard for a tournament."""
        is_member = await self.org_service.is_member(user, organization_id)
        if not is_member:
            logger.warning(
                "Unauthorized get_leaderboard by user %s", getattr(user, "id", None)
            )
            return []

        tournament = await self.repo.get_by_id(tournament_id, organization_id)
        if not tournament:
            return []

        await tournament.fetch_related("pools")

        # Get all user IDs who have participated
        all_races = await AsyncTournamentRace.filter(
            tournament_id=tournament_id
        ).values("user_id")
        user_ids = list(set(r["user_id"] for r in all_races))

        # Batch fetch all users to avoid N+1 queries
        users_dict = {u.id: u for u in await User.filter(id__in=user_ids).all()}

        leaderboard: List[LeaderboardEntry] = []

        for user_id in user_ids:
            races_list: List[Optional[AsyncTournamentRace]] = []

            # For each pool, get runs_per_pool races
            for pool in tournament.pools:
                pool_races = (
                    await AsyncTournamentRace.filter(
                        user_id=user_id,
                        tournament_id=tournament_id,
                        permalink__pool_id=pool.id,
                        status__in=["finished", "forfeit", "disqualified"],
                        reattempted=False,
                    )
                    .order_by("-score")
                    .limit(tournament.runs_per_pool)
                )

                for i in range(tournament.runs_per_pool):
                    try:
                        races_list.append(pool_races[i])
                    except IndexError:
                        races_list.append(None)

            participant_user = users_dict.get(user_id)
            if participant_user:
                entry = LeaderboardEntry(user=participant_user, races=races_list)
                leaderboard.append(entry)

        # Sort by score descending
        leaderboard.sort(key=lambda e: e.score, reverse=True)

        logger.info(
            "Generated leaderboard for tournament %s with %s entries",
            tournament_id,
            len(leaderboard),
        )
        return leaderboard

    # Review operations

    async def get_review_queue(
        self,
        user: Optional[User],
        organization_id: int,
        tournament_id: int,
        status: Optional[str] = None,
        review_status: Optional[str] = None,
        reviewed_by_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AsyncTournamentRace]:
        """
        Get review queue for a tournament.

        Only users with ASYNC_REVIEWER or ADMIN permissions can access the review queue.
        These users can see all runs regardless of hide_results setting.

        Args:
            user: User making the request
            organization_id: Organization ID
            tournament_id: Tournament ID
            status: Optional race status filter
            review_status: Optional review status filter
            reviewed_by_id: Optional reviewer filter (-1 for unreviewed)
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of races in review queue, or empty list if unauthorized
        """
        # Check authorization
        if not await self.can_review_async_races(user, organization_id):
            logger.warning(
                "Unauthorized review queue access by user %s for org %s",
                user.id if user else None,
                organization_id,
            )
            return []

        return await self.repo.get_review_queue(
            tournament_id=tournament_id,
            organization_id=organization_id,
            status=status,
            review_status=review_status,
            reviewed_by_id=reviewed_by_id,
            skip=skip,
            limit=limit,
        )

    async def get_race_for_review(
        self,
        user: Optional[User],
        organization_id: int,
        race_id: int,
    ) -> Optional[AsyncTournamentRace]:
        """
        Get a race for review with full details.

        Only users with ASYNC_REVIEWER or ADMIN permissions can review races.

        Args:
            user: User making the request
            organization_id: Organization ID
            race_id: Race ID

        Returns:
            Race with details, or None if not found/unauthorized
        """
        # Check authorization
        if not await self.can_review_async_races(user, organization_id):
            logger.warning(
                "Unauthorized race review access by user %s for race %s",
                user.id if user else None,
                race_id,
            )
            return None

        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race:
            return None

        # Prefetch related data
        await race.fetch_related(
            "user", "reviewed_by", "permalink", "permalink__pool", "tournament"
        )
        return race

    async def update_race_review(
        self,
        user: Optional[User],
        organization_id: int,
        race_id: int,
        review_status: str,
        reviewer_notes: Optional[str] = None,
        elapsed_time_seconds: Optional[int] = None,
    ) -> Optional[AsyncTournamentRace]:
        """
        Update review status and details for a race.

        Only users with ASYNC_REVIEWER or ADMIN permissions can review races.
        Users cannot review their own races.

        Args:
            user: User making the request
            organization_id: Organization ID
            race_id: Race ID
            review_status: New review status ('pending', 'accepted', 'rejected')
            reviewer_notes: Optional notes from reviewer
            elapsed_time_seconds: Optional elapsed time override (for corrections)

        Returns:
            Updated race, or None if not found/unauthorized
        """
        # Check authorization
        if not await self.can_review_async_races(user, organization_id):
            logger.warning(
                "Unauthorized race review update by user %s for race %s",
                user.id if user else None,
                race_id,
            )
            return None

        # Get the race
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race:
            return None

        # Prevent self-review
        if user and race.user_id == user.id:
            logger.warning(
                "User %s attempted to review their own race %s", user.id, race_id
            )
            return None

        # Only allow review of finished races that haven't been reattempted
        if race.status != "finished" or race.reattempted:
            logger.warning(
                "Cannot review race %s with status %s (reattempted=%s)",
                race_id,
                race.status,
                race.reattempted,
            )
            return None

        # Calculate elapsed time override if provided
        elapsed_time_override = None
        if elapsed_time_seconds is not None:
            elapsed_time_override = timedelta(seconds=elapsed_time_seconds)

        # Update review
        updated_race = await self.repo.update_race_review(
            race_id=race_id,
            organization_id=organization_id,
            review_status=review_status,
            reviewer_id=user.id if user else None,
            reviewer_notes=reviewer_notes,
            elapsed_time_override=elapsed_time_override,
        )

        if updated_race:
            # Create audit log
            await self.repo.create_audit_log(
                tournament_id=updated_race.tournament_id,
                action="review_race",
                details=f"Race {race_id} reviewed: {review_status}",
                user_id=user.id if user else None,
            )

            # Emit race review event
            if review_status == "accepted":
                event = RaceApprovedEvent(
                    entity_id=race_id,
                    user_id=user.id if user else None,
                    organization_id=organization_id,
                    tournament_id=updated_race.tournament_id,
                    racer_user_id=updated_race.user_id,
                    reviewer_user_id=user.id if user else None,
                )
                await EventBus.emit(event)
                logger.debug("Emitted RaceApprovedEvent for race %s", race_id)
            elif review_status == "rejected":
                event = RaceRejectedEvent(
                    entity_id=race_id,
                    user_id=user.id if user else None,
                    organization_id=organization_id,
                    tournament_id=updated_race.tournament_id,
                    racer_user_id=updated_race.user_id,
                    reviewer_user_id=user.id if user else None,
                    reason=reviewer_notes,
                )
                await EventBus.emit(event)
                logger.debug("Emitted RaceRejectedEvent for race %s", race_id)

            # If elapsed time was corrected, recalculate scores
            if elapsed_time_override:
                await self.calculate_permalink_scores(
                    updated_race.permalink_id, organization_id
                )

        return updated_race

    async def get_race_by_thread_id(
        self, user: Optional[User], discord_thread_id: int
    ) -> Optional[AsyncTournamentRace]:
        """
        Get a race by Discord thread ID.

        Validates that the user is the race participant.

        Args:
            user: User making the request
            discord_thread_id: Discord thread ID

        Returns:
            Race if found and user is participant, None otherwise
        """
        if not user:
            logger.warning(
                "Unauthenticated race lookup by thread_id %s", discord_thread_id
            )
            return None

        # Get race from repository
        race = await self.repo.get_race_by_thread_id(discord_thread_id)
        if not race:
            return None

        # Verify user is the race participant
        if race.user_id != user.id:
            logger.warning(
                "User %s attempted to access race %s owned by user %s",
                user.id,
                race.id,
                race.user_id,
            )
            return None

        return race

    async def update_race_submission(
        self,
        user: Optional[User],
        organization_id: int,
        race_id: int,
        runner_vod_url: Optional[str] = None,
        runner_notes: Optional[str] = None,
        review_requested_by_user: Optional[bool] = None,
        review_request_reason: Optional[str] = None,
    ) -> Optional[AsyncTournamentRace]:
        """
        Update a race submission with VoD URL, notes, and review flag.

        Only the race participant can update their own submission.

        Args:
            user: User making the request
            organization_id: Organization ID
            race_id: Race ID
            runner_vod_url: Optional VOD URL
            runner_notes: Optional runner notes/comments
            review_requested_by_user: Optional flag to request review
            review_request_reason: Optional reason for requesting review

        Returns:
            Updated race, or None if not found/unauthorized
        """
        if not user:
            logger.warning(
                "Unauthenticated race submission update attempt for race %s", race_id
            )
            return None

        # Check if user is member of organization
        if not await self.org_service.is_member(user, organization_id):
            logger.warning(
                "User %s not member of org %s for race submission update",
                user.id,
                organization_id,
            )
            return None

        # Get the race
        race = await self.repo.get_race_by_id(race_id, organization_id)
        if not race:
            return None

        # Only allow the race participant to update their submission
        if race.user_id != user.id:
            logger.warning(
                "User %s attempted to update race %s owned by user %s",
                user.id,
                race_id,
                race.user_id,
            )
            return None

        # Build update fields
        update_fields = {}
        if runner_vod_url is not None:
            update_fields["runner_vod_url"] = runner_vod_url
        if runner_notes is not None:
            update_fields["runner_notes"] = runner_notes
        if review_requested_by_user is not None:
            update_fields["review_requested_by_user"] = review_requested_by_user
            # If flagging for review, require a reason
            if review_requested_by_user and not review_request_reason:
                logger.warning(
                    "User %s attempted to flag race %s without reason", user.id, race_id
                )
                return None
        if review_request_reason is not None:
            update_fields["review_request_reason"] = review_request_reason

        # Update the race
        updated_race = await self.repo.update_race(
            race_id=race_id, organization_id=organization_id, **update_fields
        )

        if updated_race:
            # Create audit log
            action_parts = []
            if runner_vod_url is not None:
                action_parts.append("VOD URL")
            if runner_notes is not None:
                action_parts.append("notes")
            if review_requested_by_user:
                action_parts.append("flagged for review")

            action_desc = ", ".join(action_parts) if action_parts else "submission"

            await self.repo.create_audit_log(
                tournament_id=updated_race.tournament_id,
                action="update_race_submission",
                details=f"Race {race_id} submission updated: {action_desc}",
                user_id=user.id,
            )

            # Emit event for race submission update
            event = RaceSubmittedEvent(
                entity_id=race_id,
                user_id=user.id,
                organization_id=organization_id,
                tournament_id=updated_race.tournament_id,
                racer_user_id=updated_race.user_id,
            )
            await EventBus.emit(event)
            logger.debug("Emitted RaceSubmittedEvent for race %s", race_id)

            logger.info(
                "User %s updated race %s submission: %s", user.id, race_id, action_desc
            )

        return updated_race
