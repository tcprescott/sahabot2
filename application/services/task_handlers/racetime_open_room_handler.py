"""
RaceTime.gg room opening task handler.

This handler opens race rooms on racetime.gg for scheduled tournament matches.
"""
import logging
from datetime import datetime, timezone, timedelta
from models.scheduled_task import ScheduledTask
from models import Match, Tournament
from application.services.racetime_room_service import RacetimeRoomService

logger = logging.getLogger(__name__)


async def handle_racetime_open_room(task: ScheduledTask) -> None:
    """
    Handler for automatically opening racetime.gg race rooms for scheduled matches.

    This is a built-in task that runs periodically (every 5 minutes recommended) to check
    for matches that need race rooms opened. It creates rooms for matches that:
    - Are scheduled within the tournament's room_open_minutes_before window
    - Have racetime_auto_create_rooms enabled on the tournament
    - Have a RaceTime bot configured and running
    - Don't already have a race room created
    - (Optionally) All players have RaceTime accounts linked

    This task is organization-scoped but checks ALL matches across ALL tournaments
    in the organization.

    Expected task_config: {} (no config needed - task checks all scheduled matches)

    Args:
        task: ScheduledTask to execute
    """
    logger.info("Running racetime room auto-creation check (task: %s)", task.name)

    try:
        # Get the organization from the task
        if not task.organization_id:
            logger.error("Task has no organization set - cannot process")
            return

        # Find matches that need rooms opened
        now = datetime.now(timezone.utc)

        # Query tournaments with auto-create enabled in this organization
        tournaments = await Tournament.filter(
            organization_id=task.organization_id,
            is_active=True,
            racetime_auto_create_rooms=True,
            racetime_bot_id__isnull=False,
        ).prefetch_related('racetime_bot')

        if not tournaments:
            logger.debug("No tournaments with auto-create enabled in organization %s", task.organization_id)
            return

        logger.info("Found %d tournaments with auto-create enabled", len(tournaments))

        service = RacetimeRoomService()
        rooms_created = 0

        # Check each tournament's matches
        for tournament in tournaments:
            # Calculate the time window for opening rooms
            minutes_before = tournament.room_open_minutes_before
            earliest_time = now
            latest_time = now + timedelta(minutes=minutes_before)

            logger.debug(
                "Checking matches for tournament %s (window: now to %d minutes from now)",
                tournament.name,
                minutes_before
            )

            # Find matches scheduled in the window that don't have rooms yet
            matches = await Match.filter(
                tournament_id=tournament.id,
                scheduled_at__gte=earliest_time,
                scheduled_at__lte=latest_time,
                racetime_room_slug__isnull=True,  # No room created yet
                racetime_auto_create=True,  # Auto-create enabled for this match
            ).prefetch_related('players__user')

            logger.info("Found %d matches needing rooms for tournament %s", len(matches), tournament.name)

            # Create rooms for each match
            for match in matches:
                # Use a system user for the event (task execution is automated)
                # Get the first active user in the organization as the "creator"
                from models import OrganizationMember
                member = await OrganizationMember.filter(
                    organization_id=task.organization_id
                ).prefetch_related('user').first()

                if not member:
                    logger.warning("No users found in organization %s - skipping room creation", task.organization_id)
                    continue

                system_user = member.user

                # Check if room should be created
                if await service.should_create_room_for_match(match):
                    logger.info(
                        "Creating room for match %s (scheduled: %s)",
                        match.id,
                        match.scheduled_at
                    )

                    # Create the race room
                    room_slug = await service.create_race_room_for_match(
                        match=match,
                        tournament=tournament,
                        current_user=system_user,
                    )

                    if room_slug:
                        rooms_created += 1
                        logger.info("Successfully created room: %s", room_slug)
                    else:
                        logger.error("Failed to create room for match %s", match.id)

        logger.info("Racetime room auto-creation complete: %d rooms created", rooms_created)

    except Exception as e:
        logger.error("Error in racetime room auto-creation: %s", e, exc_info=True)
        raise
