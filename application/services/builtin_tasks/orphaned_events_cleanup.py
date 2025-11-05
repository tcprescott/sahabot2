"""
Scheduled task for cleaning up orphaned Discord scheduled events.

This task runs every 6 hours to clean up orphaned events that should no longer exist:
- Events for finished matches
- Events for tournaments with scheduled events disabled
- Events for deleted matches
"""

import logging
from datetime import datetime, timezone

from models import Organization, SYSTEM_USER_ID
from application.services.discord_scheduled_event_service import DiscordScheduledEventService

logger = logging.getLogger(__name__)


async def cleanup_orphaned_discord_events() -> dict:
    """
    Clean up orphaned Discord scheduled events across all organizations.

    This task:
    1. Finds all active organizations
    2. Cleans up orphaned events for each organization
    3. Reports statistics on deleted events

    Returns:
        dict: Statistics about the cleanup operation
    """
    logger.info("Starting orphaned Discord scheduled events cleanup task")

    service = DiscordScheduledEventService()

    # Find all active organizations
    organizations = await Organization.filter(is_active=True).all()

    logger.info("Found %d active organizations to check for orphaned events", len(organizations))

    total_deleted = 0
    total_errors = 0

    for org in organizations:
        try:
            logger.debug("Cleaning up orphaned events for org %s", org.id)

            # Clean up orphaned events for this organization
            stats = await service.cleanup_orphaned_events(
                user_id=SYSTEM_USER_ID,
                organization_id=org.id,
            )

            total_deleted += stats.get('deleted', 0)
            total_errors += stats.get('errors', 0)

            if stats.get('deleted', 0) > 0:
                logger.info(
                    "Org %s cleanup: %d deleted, %d errors",
                    org.id,
                    stats.get('deleted', 0),
                    stats.get('errors', 0),
                )

        except Exception as e:
            logger.exception("Error cleaning up orphaned events for org %s: %s", org.id, e)
            total_errors += 1

    logger.info(
        "Orphaned Discord events cleanup complete: %d deleted, %d errors across %d organizations",
        total_deleted,
        total_errors,
        len(organizations),
    )

    return {
        'organizations_processed': len(organizations),
        'events_deleted': total_deleted,
        'errors': total_errors,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


# Task metadata for scheduler registration
TASK_NAME = "cleanup_orphaned_discord_events"
TASK_DESCRIPTION = "Clean up orphaned Discord scheduled events for finished/disabled tournaments"
TASK_SCHEDULE = "0 */6 * * *"  # Every 6 hours at :00
TASK_ENABLED = True
TASK_FUNCTION = cleanup_orphaned_discord_events
