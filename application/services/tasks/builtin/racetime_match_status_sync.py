"""
Scheduled task for syncing match status from RaceTime.gg.

This failsafe task runs periodically to ensure match statuses are in sync with
their associated RaceTime rooms. It:
- Finds all matches with RaceTime rooms that are not in finished state
- Queries RaceTime API for current race status
- Updates match status if race has progressed (e.g., started or finished)
- Handles cases where normal event processing may have failed

This is a failsafe mechanism - normal status updates happen via event listeners.
"""

import logging
from datetime import datetime, timezone

from models import Match, SYSTEM_USER_ID
from application.events import EventBus, MatchFinishedEvent

logger = logging.getLogger(__name__)


async def sync_racetime_match_status() -> dict:
    """
    Sync match status from RaceTime.gg for all active race rooms.

    This failsafe task:
    1. Finds all matches with RaceTime rooms that aren't finished
    2. Queries RaceTime API for current race status
    3. Updates match status if race has progressed
    4. Reports statistics on updated matches

    Returns:
        dict: Statistics about the sync operation
    """
    logger.info("Starting RaceTime match status sync task")

    # Import here to avoid circular dependency
    import aiohttp
    from config import Settings
    
    settings = Settings()

    # Find all matches with RaceTime rooms that are not finished
    matches = await Match.filter(
        racetime_room_slug__isnull=False,
        finished_at__isnull=True,
    ).select_related('tournament').all()

    logger.info("Found %d matches with active RaceTime rooms", len(matches))

    total_checked_in = 0
    total_started = 0
    total_finished = 0
    total_cancelled = 0
    total_errors = 0

    async with aiohttp.ClientSession() as session:
        for match in matches:
            try:
                # Parse room slug to get category and room name
                # Format: "category/room-name"
                parts = match.racetime_room_slug.split('/', 1)
                if len(parts) != 2:
                    logger.warning("Invalid room slug format for match %s: %s", match.id, match.racetime_room_slug)
                    total_errors += 1
                    continue

                category, room_name = parts

                # Query RaceTime API for race data
                url = f"{settings.RACETIME_URL}/{category}/{room_name}/data"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning("Failed to fetch RaceTime data for match %s (room %s): HTTP %d", 
                                     match.id, match.racetime_room_slug, response.status)
                        total_errors += 1
                        continue

                    race_data = await response.json()

                # Get race status
                race_status = race_data.get('status', {}).get('value') if race_data else None

                if not race_status:
                    logger.warning("No status in RaceTime data for match %s (room %s)", 
                                 match.id, match.racetime_room_slug)
                    total_errors += 1
                    continue

                # Update match status based on race status
                now = datetime.now(timezone.utc)
                updated = False

                # If race is cancelled, unlink the room from the match
                if race_status == 'cancelled':
                    match.racetime_room_slug = None
                    updated = True
                    total_cancelled += 1
                    logger.info("Race cancelled - unlinked RaceTime room from match %s", match.id)

                # If race is open/invitational/pending and match not checked in yet
                elif race_status in ['open', 'invitational', 'pending'] and not match.checked_in_at:
                    match.checked_in_at = now
                    updated = True
                    total_checked_in += 1
                    logger.info("Auto-checked-in match %s (room %s, status: %s)", 
                              match.id, match.racetime_room_slug, race_status)

                # If race is in progress and match not started yet
                elif race_status == 'in_progress' and not match.started_at:
                    if not match.checked_in_at:
                        match.checked_in_at = now
                        total_checked_in += 1
                    match.started_at = now
                    updated = True
                    total_started += 1
                    logger.info("Auto-started match %s (room %s)", 
                              match.id, match.racetime_room_slug)

                # If race is finished and match not finished yet
                elif race_status == 'finished' and not match.finished_at:
                    if not match.checked_in_at:
                        match.checked_in_at = now
                        total_checked_in += 1
                    if not match.started_at:
                        match.started_at = now
                        total_started += 1
                    match.finished_at = now
                    updated = True
                    total_finished += 1
                    logger.info("Auto-finished match %s (room %s)", 
                              match.id, match.racetime_room_slug)

                    # Emit MatchFinishedEvent
                    await EventBus.emit(MatchFinishedEvent(
                        user_id=SYSTEM_USER_ID,
                        organization_id=match.tournament.organization_id,
                        entity_id=match.id,
                        match_id=match.id,
                        tournament_id=match.tournament_id,
                    ))

                if updated:
                    await match.save()

            except Exception as e:
                logger.exception("Error syncing status for match %s (room %s): %s", 
                               match.id, match.racetime_room_slug, e)
                total_errors += 1

    logger.info(
        "RaceTime match status sync complete: %d checked in, %d started, %d finished, %d cancelled, %d errors",
        total_checked_in,
        total_started,
        total_finished,
        total_cancelled,
        total_errors,
    )

    return {
        'matches_processed': len(matches),
        'matches_checked_in': total_checked_in,
        'matches_started': total_started,
        'matches_finished': total_finished,
        'matches_cancelled': total_cancelled,
        'errors': total_errors,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


# Task metadata for scheduler registration
TASK_NAME = "sync_racetime_match_status"
TASK_DESCRIPTION = "Failsafe sync of match status from RaceTime.gg race rooms"
TASK_SCHEDULE = "*/15 * * * *"  # Every 15 minutes
TASK_ENABLED = True
TASK_FUNCTION = sync_racetime_match_status
