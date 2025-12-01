"""
Discord domain event listeners.

Handles Discord scheduled events for tournament matches.
Priority: NORMAL - runs after audit logging.
"""

import logging
from application.events import (
    EventBus,
    EventPriority,
    MatchScheduledEvent,
    MatchUpdatedEvent,
    MatchDeletedEvent,
    MatchCompletedEvent,
)

logger = logging.getLogger(__name__)


@EventBus.on(MatchScheduledEvent, priority=EventPriority.NORMAL)
async def create_discord_event_for_match(event: MatchScheduledEvent) -> None:
    """Create Discord scheduled event when a match is scheduled."""
    from application.services.discord.discord_scheduled_event_service import (
        DiscordScheduledEventService,
    )

    service = DiscordScheduledEventService()

    try:
        await service.create_event_for_match(
            user_id=event.user_id,
            organization_id=event.organization_id,
            match_id=event.entity_id,
        )
        logger.debug("Created Discord event for match %s", event.entity_id)
    except Exception as e:
        logger.exception(
            "Failed to create Discord event for match %s: %s", event.entity_id, e
        )


@EventBus.on(MatchUpdatedEvent, priority=EventPriority.NORMAL)
async def update_discord_event_for_match(event: MatchUpdatedEvent) -> None:
    """Update Discord scheduled event when match details change."""
    from application.services.discord.discord_scheduled_event_service import (
        DiscordScheduledEventService,
    )

    # Only update Discord event if relevant fields changed
    relevant_fields = {"scheduled_at", "title", "stream_channel_id", "comment"}
    changed_fields = set(event.changed_fields or [])

    if not changed_fields.intersection(relevant_fields):
        logger.debug(
            "Match %s updated but no relevant fields changed, skipping Discord event update",
            event.entity_id,
        )
        return

    service = DiscordScheduledEventService()

    try:
        await service.update_event_for_match(
            user_id=event.user_id,
            organization_id=event.organization_id,
            match_id=event.entity_id,
        )
        logger.debug("Updated Discord event for match %s", event.entity_id)
    except Exception as e:
        logger.exception(
            "Failed to update Discord event for match %s: %s", event.entity_id, e
        )


@EventBus.on(MatchDeletedEvent, priority=EventPriority.NORMAL)
async def delete_discord_event_for_match(event: MatchDeletedEvent) -> None:
    """Delete Discord scheduled event when a match is deleted."""
    from application.services.discord.discord_scheduled_event_service import (
        DiscordScheduledEventService,
    )

    service = DiscordScheduledEventService()

    try:
        await service.delete_event_for_match(
            user_id=event.user_id,
            organization_id=event.organization_id,
            match_id=event.entity_id,
        )
        logger.debug("Deleted Discord event for match %s", event.entity_id)
    except Exception as e:
        logger.exception(
            "Failed to delete Discord event for match %s: %s", event.entity_id, e
        )


@EventBus.on(MatchCompletedEvent, priority=EventPriority.NORMAL)
async def cleanup_discord_event_for_completed_match(event: MatchCompletedEvent) -> None:
    """Clean up Discord scheduled event when a match is completed."""
    from application.services.discord.discord_scheduled_event_service import (
        DiscordScheduledEventService,
    )

    service = DiscordScheduledEventService()

    try:
        await service.delete_event_for_match(
            user_id=event.user_id,
            organization_id=event.organization_id,
            match_id=event.entity_id,
        )
        logger.debug("Cleaned up Discord event for completed match %s", event.entity_id)
    except Exception as e:
        logger.exception(
            "Failed to clean up Discord event for match %s: %s", event.entity_id, e
        )


logger.debug("Discord event listeners registered")
