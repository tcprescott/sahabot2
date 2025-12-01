"""Service layer for Async Tournament Live Races.

Handles scheduled, open-participation races on RaceTime.gg for async tournaments.
Contains org-scoped business logic, authorization checks, and event emissions.
"""

from __future__ import annotations
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import logging

from models import User, SYSTEM_USER_ID
from models.async_tournament import (
    AsyncQualifierPool,
    AsyncQualifierPermalink,
    AsyncQualifierLiveRace,
    AsyncQualifierRace,
)
from plugins.builtin.async_qualifier.repositories.async_live_race_repository import (
    AsyncLiveRaceRepository,
)
from plugins.builtin.async_qualifier.repositories.async_qualifier_repository import (
    AsyncQualifierRepository,
)
from application.services.organizations.organization_service import OrganizationService
from application.services.authorization.authorization_service_v2 import (
    AuthorizationServiceV2,
)
from application.events import (
    EventBus,
    AsyncLiveRaceCreatedEvent,
    AsyncLiveRaceUpdatedEvent,
    AsyncLiveRaceRoomOpenedEvent,
    AsyncLiveRaceStartedEvent,
    AsyncLiveRaceFinishedEvent,
    AsyncLiveRaceCancelledEvent,
)

logger = logging.getLogger(__name__)


@dataclass
class LiveRaceEligibility:
    """Represents a player's eligibility for a live race."""

    user: User
    is_eligible: bool
    reason: Optional[str] = None


class AsyncLiveRaceService:
    """Business logic for async tournament live races with organization scoping."""

    def __init__(self) -> None:
        self.repo = AsyncLiveRaceRepository()
        self.tournament_repo = AsyncQualifierRepository()
        self.org_service = OrganizationService()
        self.auth = AuthorizationServiceV2()

    async def can_manage_live_races(
        self, user: Optional[User], organization_id: int
    ) -> bool:
        """
        Check if user can manage live races in the organization.

        Requires ASYNC_TOURNAMENT_ADMIN or ADMIN permission.
        """
        if not user:
            return False
        return await self.auth.can(
            user,
            action=self.auth.get_action_for_operation("async_live_race", "manage"),
            resource=self.auth.get_resource_identifier("async_live_race", "*"),
            organization_id=organization_id,
        )

    async def can_review_races(
        self, user: Optional[User], organization_id: int
    ) -> bool:
        """
        Check if user can review/record race results.

        Requires ASYNC_REVIEWER, ASYNC_TOURNAMENT_ADMIN, or ADMIN permission.
        """
        if not user:
            return False
        # Delegate to organization service
        return await self.org_service.user_can_review_async_races(user, organization_id)

    # =========================================================================
    # Admin Operations
    # =========================================================================

    async def create_live_race(
        self,
        current_user: User,
        organization_id: int,
        tournament_id: int,
        pool_id: int,
        scheduled_at: datetime,
        match_title: Optional[str] = None,
        permalink_id: Optional[int] = None,
        episode_id: Optional[int] = None,
        race_room_profile_id: Optional[int] = None,
    ) -> AsyncQualifierLiveRace:
        """
        Create a new scheduled live race.

        Args:
            current_user: User creating the live race
            organization_id: Organization ID for scoping
            tournament_id: Tournament to associate with
            pool_id: Pool for this race
            scheduled_at: When the race is scheduled to start
            match_title: Optional display name for the race
            permalink_id: Optional specific seed/permalink to use
            episode_id: Optional SpeedGaming episode ID
            race_room_profile_id: Optional race room profile override

        Returns:
            Created AsyncQualifierLiveRace

        Raises:
            PermissionError: If user lacks ASYNC_TOURNAMENT_ADMIN permission
            ValueError: If tournament/pool not found or doesn't belong to organization
        """
        # Authorization check
        if not await self.can_manage_live_races(current_user, organization_id):
            logger.warning(
                "User %s denied creating live race - lacks permission in org %s",
                current_user.id,
                organization_id,
            )
            raise PermissionError("You do not have permission to create live races")

        # Validate tournament belongs to organization
        tournament = await self.tournament_repo.get_by_id(
            tournament_id, organization_id
        )
        if not tournament:
            raise ValueError("Tournament not found or does not belong to organization")

        # Validate pool belongs to tournament
        pool = await AsyncQualifierPool.get_or_none(
            id=pool_id, tournament_id=tournament_id
        )
        if not pool:
            raise ValueError("Pool not found or does not belong to tournament")

        # Validate permalink if provided
        if permalink_id:
            permalink = await AsyncQualifierPermalink.get_or_none(id=permalink_id)
            if not permalink:
                raise ValueError("Permalink not found")

        # Create the live race
        live_race = await self.repo.create_live_race(
            tournament_id=tournament_id,
            pool_id=pool_id,
            scheduled_at=scheduled_at,
            match_title=match_title,
            permalink_id=permalink_id,
            episode_id=episode_id,
            race_room_profile_id=race_room_profile_id,
        )

        logger.info(
            "Live race %s created for tournament %s by user %s",
            live_race.id,
            tournament_id,
            current_user.id,
        )

        # Schedule task to open room before scheduled time
        if scheduled_at:
            await self._schedule_room_open_task(live_race, current_user)

        # Emit event
        await EventBus.emit(
            AsyncLiveRaceCreatedEvent(
                user_id=current_user.id,
                organization_id=organization_id,
                entity_id=live_race.id,
                tournament_id=tournament_id,
                pool_id=pool_id,
                scheduled_at=scheduled_at.isoformat() if scheduled_at else None,
                match_title=match_title,
            )
        )

        return live_race

    async def _schedule_room_open_task(
        self,
        live_race: AsyncQualifierLiveRace,
        creating_user: User,
    ) -> None:
        """
        Schedule a task to open the race room before the scheduled time.

        Creates a ONE_TIME task to run 30 minutes before the scheduled race time.

        Args:
            live_race: Live race to schedule task for
            creating_user: User who created the live race (for authorization)
        """
        if not live_race.scheduled_at:
            logger.warning(
                "Cannot schedule room open task for live race %s - no scheduled_at",
                live_race.id,
            )
            return

        # Schedule room open 30 minutes before race time
        room_open_time = live_race.scheduled_at - timedelta(minutes=30)

        # Import here to avoid circular dependency
        from application.services.tasks.task_scheduler_service import (
            TaskSchedulerService,
        )
        from models.scheduled_task import TaskType, ScheduleType

        task_service = TaskSchedulerService()

        # Ensure we have organization_id
        await live_race.fetch_related("tournament")

        await task_service.create_task(
            user=creating_user,
            name=f"Open room for live race {live_race.id}",
            description=f"Open RaceTime.gg room for live race: {live_race.match_title or 'Untitled'}",
            task_type=TaskType.ASYNC_LIVE_RACE_OPEN,
            schedule_type=ScheduleType.ONE_TIME,
            organization_id=live_race.tournament.organization_id,
            scheduled_time=room_open_time,
            task_config={
                "live_race_id": live_race.id,
                "organization_id": live_race.tournament.organization_id,
            },
        )

        logger.info(
            "Scheduled room open task for live race %s at %s",
            live_race.id,
            room_open_time.isoformat(),
        )

    async def update_live_race(
        self,
        current_user: User,
        organization_id: int,
        live_race_id: int,
        **updates,
    ) -> AsyncQualifierLiveRace:
        """
        Update a live race.

        Args:
            current_user: User updating the live race
            organization_id: Organization ID for scoping
            live_race_id: Live race to update
            **updates: Fields to update (scheduled_at, match_title, etc.)

        Returns:
            Updated AsyncQualifierLiveRace

        Raises:
            PermissionError: If user lacks ASYNC_TOURNAMENT_ADMIN permission
            ValueError: If live race not found or already in progress
        """
        # Authorization check
        if not await self.can_manage_live_races(current_user, organization_id):
            logger.warning(
                "User %s denied updating live race %s - lacks permission",
                current_user.id,
                live_race_id,
            )
            raise PermissionError("You do not have permission to update live races")

        # Get and validate live race
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError("Live race not found")

        # Validate organization ownership via tournament
        await live_race.fetch_related("tournament")
        if live_race.tournament.organization_id != organization_id:
            raise ValueError("Live race does not belong to organization")

        # Don't allow updates to in-progress or finished races
        if live_race.status in ["in_progress", "finished"]:
            raise ValueError(f"Cannot update race with status: {live_race.status}")

        # Update the live race
        updated = await self.repo.update_live_race(live_race_id, **updates)

        logger.info(
            "Live race %s updated by user %s: %s",
            live_race_id,
            current_user.id,
            list(updates.keys()),
        )

        # Emit event
        await EventBus.emit(
            AsyncLiveRaceUpdatedEvent(
                user_id=current_user.id,
                organization_id=organization_id,
                entity_id=live_race_id,
                tournament_id=live_race.tournament_id,
                changed_fields=list(updates.keys()),
            )
        )

        return updated

    async def cancel_live_race(
        self,
        current_user: User,
        organization_id: int,
        live_race_id: int,
        reason: Optional[str] = None,
    ) -> AsyncQualifierLiveRace:
        """
        Cancel a scheduled or pending live race.

        Args:
            current_user: User cancelling the race
            organization_id: Organization ID for scoping
            live_race_id: Live race to cancel
            reason: Optional reason for cancellation

        Returns:
            Cancelled AsyncQualifierLiveRace

        Raises:
            PermissionError: If user lacks ASYNC_TOURNAMENT_ADMIN permission
            ValueError: If live race not found or already finished
        """
        # Authorization check
        if not await self.can_manage_live_races(current_user, organization_id):
            logger.warning(
                "User %s denied cancelling live race %s - lacks permission",
                current_user.id,
                live_race_id,
            )
            raise PermissionError("You do not have permission to cancel live races")

        # Get and validate live race
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError("Live race not found")

        # Validate organization ownership
        await live_race.fetch_related("tournament")
        if live_race.tournament.organization_id != organization_id:
            raise ValueError("Live race does not belong to organization")

        # Don't allow cancelling finished races
        if live_race.status == "finished":
            raise ValueError("Cannot cancel a finished race")

        # Update status to cancelled
        cancelled = await self.repo.update_live_race(live_race_id, status="cancelled")

        logger.info(
            "Live race %s cancelled by user %s: %s",
            live_race_id,
            current_user.id,
            reason or "No reason provided",
        )

        # Emit event
        await EventBus.emit(
            AsyncLiveRaceCancelledEvent(
                user_id=current_user.id,
                organization_id=organization_id,
                entity_id=live_race_id,
                tournament_id=live_race.tournament_id,
                reason=reason,
            )
        )

        return cancelled

    async def delete_live_race(
        self,
        current_user: User,
        organization_id: int,
        live_race_id: int,
    ) -> None:
        """
        Delete a live race (hard delete).

        Only allows deleting races that haven't started yet.

        Args:
            current_user: User deleting the live race
            organization_id: Organization ID for scoping
            live_race_id: Live race to delete

        Raises:
            PermissionError: If user lacks ASYNC_TOURNAMENT_ADMIN permission
            ValueError: If live race not found or has started
        """
        # Authorization check
        if not await self.can_manage_live_races(current_user, organization_id):
            logger.warning(
                "User %s denied deleting live race %s - lacks permission",
                current_user.id,
                live_race_id,
            )
            raise PermissionError("You do not have permission to delete live races")

        # Get and validate live race
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError("Live race not found")

        # Validate organization ownership
        await live_race.fetch_related("tournament")
        if live_race.tournament.organization_id != organization_id:
            raise ValueError("Live race does not belong to organization")

        # Only allow deleting scheduled or cancelled races
        if live_race.status not in ["scheduled", "cancelled"]:
            raise ValueError(f"Cannot delete race with status: {live_race.status}")

        # Delete the live race
        await self.repo.delete_live_race(live_race_id)

        logger.info(
            "Live race %s deleted by user %s",
            live_race_id,
            current_user.id,
        )

    # =========================================================================
    # Race Management
    # =========================================================================

    async def open_race_room(
        self,
        live_race_id: int,
    ) -> AsyncQualifierLiveRace:
        """
        Open a RaceTime.gg room for a live race.

        Called by the task scheduler before the scheduled time.
        Creates the race room and updates the live race status.

        Args:
            live_race_id: Live race to open room for

        Returns:
            Updated AsyncQualifierLiveRace with racetime_slug

        Raises:
            ValueError: If live race not found or already opened
        """
        # Get live race with all relations
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError("Live race not found")

        # Check status
        if live_race.status != "scheduled":
            raise ValueError(
                f"Cannot open room for race with status: {live_race.status}"
            )

        # Get tournament and organization for RaceTime.gg integration
        await live_race.fetch_related("tournament", "tournament__organization", "pool")

        # Get effective race room profile
        profile = await live_race.get_effective_profile()

        # Import RaceTime bot functions
        from racetime.client import get_racetime_bot_instance
        from racetime.handlers.live_race_handler import AsyncLiveRaceHandler

        # Get category from tournament (async tournaments use alttpr category)
        category = "alttpr"  # Could be made configurable per tournament in future

        # Get bot instance for this category
        bot = get_racetime_bot_instance(category)
        if not bot:
            raise ValueError(f"RaceTime bot not running for category: {category}")

        # Build race room parameters from profile
        race_params = self._profile_to_race_params(
            profile=profile,
            goal=live_race.match_title or f"Live Race - {live_race.tournament.name}",
            info_user=None,  # Could add organizer info in future
        )

        # Create race room on RaceTime.gg
        try:
            handler = await bot.startrace(**race_params)

            # Ensure handler is our custom AsyncLiveRaceHandler
            if not isinstance(handler, AsyncLiveRaceHandler):
                # Replace with live race handler
                handler.should_stop = True  # Stop the generic handler

                # Create new live race handler
                handler = AsyncLiveRaceHandler(
                    live_race_id=live_race_id, **bot.create_handler_kwargs(handler.data)
                )
                await handler.begin()

            racetime_slug = handler.data.get("name", "")
        except Exception as e:
            logger.error(
                "Failed to create RaceTime room for live race %s: %s",
                live_race_id,
                e,
                exc_info=True,
            )
            raise ValueError(f"Failed to create RaceTime room: {e}") from e

        # Update live race with room details
        updated = await self.repo.update_live_race(
            live_race_id,
            racetime_slug=racetime_slug,
            room_open_time=datetime.now(timezone.utc),
            status="pending",
        )

        logger.info(
            "Race room opened for live race %s: %s",
            live_race_id,
            racetime_slug,
        )

        # Emit event
        await EventBus.emit(
            AsyncLiveRaceRoomOpenedEvent(
                user_id=SYSTEM_USER_ID,  # System action
                organization_id=live_race.tournament.organization_id,
                entity_id=live_race_id,
                tournament_id=live_race.tournament_id,
                racetime_slug=racetime_slug,
                racetime_url=f"https://racetime.gg/{racetime_slug}",
                scheduled_at=(
                    live_race.scheduled_at.isoformat()
                    if live_race.scheduled_at
                    else None
                ),
            )
        )

        return updated

    async def process_race_start(
        self,
        live_race_id: int,
        participant_racetime_ids: List[str],
    ) -> AsyncQualifierLiveRace:
        """
        Process race start event from RaceTime.gg.

        Creates AsyncQualifierRace records for all participants.

        Args:
            live_race_id: Live race that started
            participant_racetime_ids: List of RaceTime.gg user IDs who entered

        Returns:
            Updated AsyncQualifierLiveRace

        Raises:
            ValueError: If live race not found
        """
        # Get live race
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError("Live race not found")

        # Get tournament
        await live_race.fetch_related("tournament")

        # Map RaceTime.gg IDs to User IDs
        # This will be implemented properly in Phase 3 with RaceTime user mapping
        users = await User.filter(racetime_id__in=participant_racetime_ids).all()

        if users:
            # Create race records for all participants
            await self.repo.create_participant_races(
                live_race_id, [u.id for u in users]
            )

        # Update status to in_progress
        updated = await self.repo.update_live_race(live_race_id, status="in_progress")

        logger.info(
            "Live race %s started with %s participants",
            live_race_id,
            len(users),
        )

        # Emit event
        await EventBus.emit(
            AsyncLiveRaceStartedEvent(
                user_id=SYSTEM_USER_ID,  # System action
                organization_id=live_race.tournament.organization_id,
                entity_id=live_race_id,
                tournament_id=live_race.tournament_id,
                racetime_slug=live_race.racetime_slug,
                participant_count=len(users),
            )
        )

        return updated

    async def process_race_finish(
        self,
        live_race_id: int,
        results: List[
            Tuple[str, int, str]
        ],  # (racetime_id, finish_time_seconds, status)
    ) -> AsyncQualifierLiveRace:
        """
        Process race finish event from RaceTime.gg.

        Updates AsyncQualifierRace records with finish times and statuses.

        Args:
            live_race_id: Live race that finished
            results: List of (racetime_id, finish_time_seconds, status) tuples

        Returns:
            Updated AsyncQualifierLiveRace

        Raises:
            ValueError: If live race not found
        """
        # Get live race
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError("Live race not found")

        await live_race.fetch_related("tournament")

        # Map RaceTime.gg IDs to User IDs
        racetime_ids = [r[0] for r in results]
        users_map = {
            u.racetime_id: u
            for u in await User.filter(racetime_id__in=racetime_ids).all()
        }

        # Update race records with results
        finisher_count = 0
        for racetime_id, finish_time_seconds, status in results:
            user = users_map.get(racetime_id)
            if not user:
                logger.warning("User with RaceTime ID %s not found", racetime_id)
                continue

            # Find the race record
            race = await AsyncQualifierRace.get_or_none(
                live_race_id=live_race_id,
                user_id=user.id,
            )
            if not race:
                logger.warning(
                    "Race record not found for user %s in live race %s",
                    user.id,
                    live_race_id,
                )
                continue

            # Update race record
            race.end_time = datetime.now(timezone.utc)
            race.elapsed_time = timedelta(seconds=finish_time_seconds)
            race.status = status  # 'finished', 'forfeit', 'disqualified'
            await race.save()

            if status == "finished":
                finisher_count += 1

        # Update live race status to finished
        updated = await self.repo.update_live_race(live_race_id, status="finished")

        logger.info(
            "Live race %s finished with %s finishers",
            live_race_id,
            finisher_count,
        )

        # Emit event
        await EventBus.emit(
            AsyncLiveRaceFinishedEvent(
                user_id=SYSTEM_USER_ID,  # System action
                organization_id=live_race.tournament.organization_id,
                entity_id=live_race_id,
                tournament_id=live_race.tournament_id,
                racetime_slug=live_race.racetime_slug,
                finisher_count=finisher_count,
            )
        )

        return updated

    async def record_live_race_results(
        self,
        current_user: User,
        organization_id: int,
        racetime_slug: str,
    ) -> AsyncQualifierLiveRace:
        """
        Manually record results from a RaceTime.gg race.

        Fetches race data from RaceTime.gg and processes results.

        Args:
            current_user: User recording the results
            organization_id: Organization ID for scoping
            racetime_slug: RaceTime.gg race slug to fetch results from

        Returns:
            Updated AsyncQualifierLiveRace

        Raises:
            PermissionError: If user lacks reviewer permission
            ValueError: If race not found or already recorded
        """
        # Authorization check
        if not await self.can_review_races(current_user, organization_id):
            logger.warning(
                "User %s denied recording results - lacks permission in org %s",
                current_user.id,
                organization_id,
            )
            raise PermissionError("You do not have permission to record race results")

        # Find live race by RaceTime slug
        live_race = await self.repo.get_by_racetime_slug(racetime_slug)
        if not live_race:
            raise ValueError(f"Live race not found for slug: {racetime_slug}")

        # Validate organization ownership
        await live_race.fetch_related("tournament")
        if live_race.tournament.organization_id != organization_id:
            raise ValueError("Live race does not belong to organization")

        # Don't allow re-recording finished races
        if live_race.status == "finished":
            raise ValueError("Race results already recorded")

        # Fetch results from RaceTime.gg
        # This will be implemented in Phase 3
        # For now, raise NotImplementedError
        raise NotImplementedError("RaceTime.gg integration not yet implemented")

    # =========================================================================
    # Participant Management
    # =========================================================================

    async def get_eligible_participants(
        self,
        organization_id: int,
        live_race_id: int,
    ) -> List[LiveRaceEligibility]:
        """
        Get list of eligible participants for a live race.

        Args:
            organization_id: Organization ID for scoping
            live_race_id: Live race to check eligibility for

        Returns:
            List of LiveRaceEligibility objects

        Raises:
            ValueError: If live race not found
        """
        # Get live race
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            raise ValueError("Live race not found")

        # Validate organization ownership
        await live_race.fetch_related("tournament")
        if live_race.tournament.organization_id != organization_id:
            raise ValueError("Live race does not belong to organization")

        # Get eligibility from repository
        eligibility_tuples = await self.repo.get_eligible_participants(live_race_id)

        # Convert to LiveRaceEligibility objects
        return [
            LiveRaceEligibility(user=user, is_eligible=eligible, reason=reason)
            for user, eligible, reason in eligibility_tuples
        ]

    async def check_player_eligibility(
        self,
        user_id: int,
        organization_id: int,
        tournament_id: int,
        pool_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a specific player is eligible for a pool.

        Args:
            user_id: User to check
            organization_id: Organization ID for scoping
            tournament_id: Tournament context
            pool_id: Pool to check eligibility for

        Returns:
            Tuple of (is_eligible, reason_if_not)
        """
        # Get tournament
        tournament = await self.tournament_repo.get_by_id(
            tournament_id, organization_id
        )
        if not tournament:
            return False, "Tournament not found"

        # Get pool
        pool = await AsyncQualifierPool.get_or_none(
            id=pool_id, tournament_id=tournament_id
        )
        if not pool:
            return False, "Pool not found"

        # Check if user is registered for tournament (if registration is enabled)
        # Note: AsyncQualifierRegistration is not yet implemented, will be added in future
        # For now, assume all organization members can participate
        # registration = await AsyncQualifierRegistration.get_or_none(
        #     tournament_id=tournament_id,
        #     user_id=user_id,
        # )
        # if not registration:
        #     return False, "Not registered for tournament"

        # Check pool availability (runs_per_pool)
        if pool.runs_per_pool is not None and pool.runs_per_pool > 0:
            # Count completed races in this pool
            finished_count = await AsyncQualifierRace.filter(
                user_id=user_id,
                permalink__pool_id=pool_id,
                status="finished",
            ).count()

            if finished_count >= pool.runs_per_pool:
                return (
                    False,
                    f"Already completed {pool.runs_per_pool} races in this pool",
                )

        # Check for active pending/in_progress races
        active_race = await AsyncQualifierRace.filter(
            user_id=user_id,
            permalink__pool__tournament_id=tournament_id,
            status__in=["pending", "in_progress"],
        ).first()

        if active_race:
            return False, "Has an active race in progress"

        return True, None

    # =========================================================================
    # Queries
    # =========================================================================

    async def get_live_race(
        self,
        organization_id: int,
        live_race_id: int,
    ) -> Optional[AsyncQualifierLiveRace]:
        """
        Get a specific live race by ID.

        Args:
            organization_id: Organization ID for scoping
            live_race_id: Live race ID

        Returns:
            AsyncQualifierLiveRace or None if not found/no access
        """
        live_race = await self.repo.get_by_id_with_relations(live_race_id)
        if not live_race:
            return None

        # Validate organization ownership
        await live_race.fetch_related("tournament")
        if live_race.tournament.organization_id != organization_id:
            return None

        return live_race

    def _profile_to_race_params(
        self,
        profile: Optional[object],
        goal: str,
        info_user: Optional[str] = None,
    ) -> dict:
        """
        Convert RaceRoomProfile to RaceTime.gg race parameters.

        Args:
            profile: RaceRoomProfile or None for defaults
            goal: Race goal text
            info_user: Optional user info to display

        Returns:
            Dictionary of parameters for bot.startrace()
        """
        params = {
            "goal": goal,
            "invitational": False,  # Live races are always open
            "unlisted": False,  # Live races are always public
        }

        if info_user:
            params["info_user"] = info_user

        if profile:
            # Map profile fields to RaceTime API parameters
            params["streaming_required"] = profile.streaming_required
            params["auto_start"] = profile.auto_start
            params["allow_comments"] = profile.allow_comments
            params["hide_comments"] = profile.hide_comments
            params["allow_prerace_chat"] = profile.allow_prerace_chat
            params["allow_midrace_chat"] = profile.allow_midrace_chat
            params["allow_non_entrant_chat"] = profile.allow_non_entrant_chat
            params["time_limit"] = profile.time_limit  # hours
            params["start_delay"] = profile.start_delay  # seconds
        else:
            # Default values when no profile
            params["streaming_required"] = False
            params["auto_start"] = True
            params["allow_comments"] = True
            params["hide_comments"] = False
            params["allow_prerace_chat"] = True
            params["allow_midrace_chat"] = True
            params["allow_non_entrant_chat"] = True
            params["time_limit"] = 24  # 24 hours
            params["start_delay"] = 15  # 15 seconds

        return params

    async def list_scheduled_races(
        self,
        organization_id: int,
        tournament_id: Optional[int] = None,
    ) -> List[AsyncQualifierLiveRace]:
        """
        Get list of upcoming scheduled live races.

        Args:
            organization_id: Organization ID for scoping
            tournament_id: Optional tournament to filter by

        Returns:
            List of upcoming AsyncQualifierLiveRace objects
        """
        return await self.repo.list_scheduled_races(
            organization_id=organization_id,
            tournament_id=tournament_id,
        )

    async def list_live_races(
        self,
        organization_id: int,
        tournament_id: int,
        status: Optional[str] = None,
    ) -> List[AsyncQualifierLiveRace]:
        """
        Get all live races for a tournament.

        Args:
            organization_id: Organization ID for scoping
            tournament_id: Tournament to get races for
            status: Optional status filter

        Returns:
            List of AsyncQualifierLiveRace objects
        """
        # Validate tournament belongs to organization
        tournament = await self.tournament_repo.get_by_id(
            tournament_id, organization_id
        )
        if not tournament:
            return []

        return await self.repo.list_races_for_tournament(
            tournament_id=tournament_id,
            status=status,
        )
