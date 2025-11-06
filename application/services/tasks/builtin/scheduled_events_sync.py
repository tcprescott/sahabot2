"""
Scheduled task for synchronizing Discord scheduled events.

This task runs hourly to ensure Discord scheduled events are in sync with
tournament match schedules. It:
- Creates missing events for tournaments with create_scheduled_events=True
- Updates events that have changed details
- Deletes orphaned events for completed/deleted matches
- Auto-updates event statuses (scheduled → active → completed/cancelled)

Note: A separate cleanup task (orphaned_events_cleanup.py) runs every 6 hours
to perform more comprehensive cleanup across all organizations.
"""

import logging
from datetime import datetime, timezone

from models import Tournament, SYSTEM_USER_ID
from application.services.discord.discord_scheduled_event_service import DiscordScheduledEventService

logger = logging.getLogger(__name__)


async def sync_discord_scheduled_events() -> dict:
    """
    Synchronize Discord scheduled events for all active tournaments.

    This task:
    1. Finds all tournaments with create_scheduled_events=True
    2. Syncs events for each tournament
    3. Reports statistics on created/updated/deleted events

    Returns:
        dict: Statistics about the sync operation
    """
    logger.info("Starting Discord scheduled events sync task")

    service = DiscordScheduledEventService()

    # Find all tournaments with scheduled events enabled
    tournaments = await Tournament.filter(
        create_scheduled_events=True,
        scheduled_events_enabled=True,
    ).all()

    logger.info("Found %d tournaments with scheduled events enabled", len(tournaments))

    total_created = 0
    total_updated = 0
    total_deleted = 0
    total_errors = 0
    total_status_updates = {
        'activated': 0,
        'completed': 0,
        'cancelled': 0,
    }

    for tournament in tournaments:
        try:
            logger.debug("Syncing events for tournament %s (org %s)", tournament.id, tournament.organization_id)

            # Sync events for this tournament (create/update/delete)
            stats = await service.sync_tournament_events(
                user_id=SYSTEM_USER_ID,
                organization_id=tournament.organization_id,
                tournament_id=tournament.id,
            )

            total_created += stats.get('created', 0)
            total_updated += stats.get('updated', 0)
            total_deleted += stats.get('deleted', 0)
            
            # Auto-update event statuses for this organization
            status_stats = await service.auto_update_event_statuses(
                organization_id=tournament.organization_id,
            )
            
            total_status_updates['activated'] += status_stats.get('activated', 0)
            total_status_updates['completed'] += status_stats.get('completed', 0)
            total_status_updates['cancelled'] += status_stats.get('cancelled', 0)

            logger.debug(
                "Tournament %s sync complete: %d created, %d updated, %d deleted, %d status updates",
                tournament.id,
                stats.get('created', 0),
                stats.get('updated', 0),
                stats.get('deleted', 0),
                sum(status_stats.values()) - status_stats.get('errors', 0),
            )

        except Exception as e:
            logger.exception("Error syncing events for tournament %s: %s", tournament.id, e)
            total_errors += 1

    logger.info(
        "Discord scheduled events sync complete: %d created, %d updated, %d deleted, %d activated, %d completed, %d cancelled, %d errors",
        total_created,
        total_updated,
        total_deleted,
        total_status_updates['activated'],
        total_status_updates['completed'],
        total_status_updates['cancelled'],
        total_errors,
    )

    return {
        'tournaments_processed': len(tournaments),
        'events_created': total_created,
        'events_updated': total_updated,
        'events_deleted': total_deleted,
        'events_activated': total_status_updates['activated'],
        'events_completed': total_status_updates['completed'],
        'events_cancelled': total_status_updates['cancelled'],
        'errors': total_errors,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


# Task metadata for scheduler registration
TASK_NAME = "sync_discord_scheduled_events"
TASK_DESCRIPTION = "Synchronize Discord scheduled events for all active tournaments"
TASK_SCHEDULE = "0 * * * *"  # Every hour at :00
TASK_ENABLED = True
TASK_FUNCTION = sync_discord_scheduled_events
