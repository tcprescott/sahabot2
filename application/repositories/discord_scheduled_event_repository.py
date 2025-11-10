"""
Repository for Discord Scheduled Event data access.

Handles database operations for Discord scheduled events linked to matches.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from models import DiscordScheduledEvent

logger = logging.getLogger(__name__)


class DiscordScheduledEventRepository:
    """Data access methods for DiscordScheduledEvent model."""

    async def create(
        self,
        scheduled_event_id: int,
        match_id: int,
        organization_id: int,
        event_slug: Optional[str] = None,
    ) -> DiscordScheduledEvent:
        """
        Create a Discord scheduled event record.

        Args:
            scheduled_event_id: Discord's event ID
            match_id: Match ID to link
            organization_id: Organization ID for tenant scoping
            event_slug: Optional slug for categorization

        Returns:
            Created DiscordScheduledEvent instance
        """
        event = await DiscordScheduledEvent.create(
            scheduled_event_id=scheduled_event_id,
            match_id=match_id,
            organization_id=organization_id,
            event_slug=event_slug,
        )
        logger.info(
            "Created Discord scheduled event %s for match %s in org %s",
            scheduled_event_id,
            match_id,
            organization_id,
        )
        return event

    async def get_by_match(
        self,
        organization_id: int,
        match_id: int,
    ) -> Optional[DiscordScheduledEvent]:
        """
        Get Discord scheduled event by match ID.

        Note: Returns the first event if multiple exist.
        Use list_for_match() to get all events for a match.

        Args:
            organization_id: Organization ID for tenant scoping
            match_id: Match ID

        Returns:
            DiscordScheduledEvent if found, None otherwise
        """
        return await DiscordScheduledEvent.get_or_none(
            match_id=match_id,
            organization_id=organization_id,
        )

    async def list_for_match(
        self,
        organization_id: int,
        match_id: int,
    ) -> list[DiscordScheduledEvent]:
        """
        Get all Discord scheduled events for a match.

        Args:
            organization_id: Organization ID for tenant scoping
            match_id: Match ID

        Returns:
            List of DiscordScheduledEvents (may be empty)
        """
        return await DiscordScheduledEvent.filter(
            match_id=match_id,
            organization_id=organization_id,
        ).all()

    async def get_by_event_id(
        self,
        organization_id: int,
        scheduled_event_id: int,
    ) -> Optional[DiscordScheduledEvent]:
        """
        Get Discord scheduled event by Discord's event ID.

        Args:
            organization_id: Organization ID for tenant scoping
            scheduled_event_id: Discord's event ID

        Returns:
            DiscordScheduledEvent if found, None otherwise
        """
        return await DiscordScheduledEvent.get_or_none(
            scheduled_event_id=scheduled_event_id,
            organization_id=organization_id,
        )

    async def list_for_tournament(
        self,
        organization_id: int,
        tournament_id: int,
    ) -> List[DiscordScheduledEvent]:
        """
        List all Discord scheduled events for a tournament.

        Args:
            organization_id: Organization ID for tenant scoping
            tournament_id: Tournament ID

        Returns:
            List of DiscordScheduledEvent instances
        """
        events = await DiscordScheduledEvent.filter(
            organization_id=organization_id,
            match__tournament_id=tournament_id,
        ).prefetch_related("match", "match__tournament")

        logger.debug(
            "Found %d Discord scheduled events for tournament %s in org %s",
            len(events),
            tournament_id,
            organization_id,
        )
        return events

    async def list_for_org(
        self,
        organization_id: int,
    ) -> List[DiscordScheduledEvent]:
        """
        List all Discord scheduled events for an organization.

        Args:
            organization_id: Organization ID for tenant scoping

        Returns:
            List of DiscordScheduledEvent instances
        """
        events = (
            await DiscordScheduledEvent.filter(
                organization_id=organization_id,
            )
            .prefetch_related("match", "match__tournament")
            .order_by("-created_at")
        )

        logger.debug(
            "Found %d Discord scheduled events in org %s",
            len(events),
            organization_id,
        )
        return events

    async def delete(
        self,
        organization_id: int,
        match_id: int,
    ) -> bool:
        """
        Delete Discord scheduled event record.

        Args:
            organization_id: Organization ID for tenant scoping
            match_id: Match ID

        Returns:
            True if deleted, False if not found
        """
        event = await self.get_by_match(organization_id, match_id)
        if not event:
            logger.warning(
                "Discord scheduled event not found for match %s in org %s",
                match_id,
                organization_id,
            )
            return False

        scheduled_event_id = event.scheduled_event_id
        await event.delete()
        logger.info(
            "Deleted Discord scheduled event %s for match %s in org %s",
            scheduled_event_id,
            match_id,
            organization_id,
        )
        return True

    async def delete_by_event_id(
        self,
        organization_id: int,
        scheduled_event_id: int,
    ) -> bool:
        """
        Delete Discord scheduled event record by event ID.

        Args:
            organization_id: Organization ID for tenant scoping
            scheduled_event_id: Discord's event ID

        Returns:
            True if deleted, False if not found
        """
        event = await self.get_by_event_id(organization_id, scheduled_event_id)
        if not event:
            logger.warning(
                "Discord scheduled event %s not found in org %s",
                scheduled_event_id,
                organization_id,
            )
            return False

        match_id = event.match_id
        await event.delete()
        logger.info(
            "Deleted Discord scheduled event %s (match %s) in org %s",
            scheduled_event_id,
            match_id,
            organization_id,
        )
        return True

    async def delete_by_id(
        self,
        event_id: int,
    ) -> bool:
        """
        Delete Discord scheduled event record by database ID.

        Args:
            event_id: Database primary key ID

        Returns:
            True if deleted, False if not found
        """
        event = await DiscordScheduledEvent.get_or_none(id=event_id)
        if not event:
            logger.warning("Discord scheduled event with ID %s not found", event_id)
            return False

        await event.delete()
        logger.info("Deleted Discord scheduled event database record %s", event_id)
        return True

    async def list_upcoming_events(
        self,
        organization_id: int,
        hours_future: int = 168,  # 7 days default
    ) -> List[DiscordScheduledEvent]:
        """
        List Discord scheduled events for upcoming matches.

        Args:
            organization_id: Organization ID for tenant scoping
            hours_future: How many hours in the future to look

        Returns:
            List of DiscordScheduledEvent instances for upcoming matches
        """
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        future_cutoff = now + timedelta(hours=hours_future)

        events = await DiscordScheduledEvent.filter(
            organization_id=organization_id,
            match__scheduled_at__lte=future_cutoff,
            match__finished_at__isnull=True,  # Only unfinished matches
        ).prefetch_related("match", "match__tournament")

        logger.debug(
            "Found %d upcoming Discord scheduled events in org %s (next %d hours)",
            len(events),
            organization_id,
            hours_future,
        )
        return events

    async def list_orphaned_events(
        self,
        organization_id: int,
    ) -> List[DiscordScheduledEvent]:
        """
        List Discord scheduled events for finished or deleted matches.

        These are "orphaned" events that should be cleaned up.

        Args:
            organization_id: Organization ID for tenant scoping

        Returns:
            List of DiscordScheduledEvent instances to clean up
        """
        # Events for finished matches
        events = await DiscordScheduledEvent.filter(
            organization_id=organization_id,
            match__finished_at__isnull=False,
        ).prefetch_related("match")

        logger.debug(
            "Found %d orphaned Discord scheduled events in org %s",
            len(events),
            organization_id,
        )
        return events

    async def list_events_for_disabled_tournaments(
        self,
        organization_id: int,
    ) -> List[DiscordScheduledEvent]:
        """
        List Discord scheduled events for tournaments with events disabled.

        These events should be cleaned up when tournaments disable the feature.

        Args:
            organization_id: Organization ID for tenant scoping

        Returns:
            List of DiscordScheduledEvent instances to clean up
        """
        # Get events for tournaments with events disabled
        events = await DiscordScheduledEvent.filter(
            organization_id=organization_id,
            match__tournament__scheduled_events_enabled=False,
        ).prefetch_related("match", "match__tournament")

        # Also check for tournaments with create_scheduled_events=False
        more_events = await DiscordScheduledEvent.filter(
            organization_id=organization_id,
            match__tournament__create_scheduled_events=False,
        ).prefetch_related("match", "match__tournament")

        # Combine and deduplicate
        all_event_ids = set()
        combined = []
        for event in events + more_events:
            if event.id not in all_event_ids:
                all_event_ids.add(event.id)
                combined.append(event)

        logger.debug(
            "Found %d Discord events for disabled tournaments in org %s",
            len(combined),
            organization_id,
        )
        return combined

    async def cleanup_all_orphaned_events(
        self,
        organization_id: int,
    ) -> List[DiscordScheduledEvent]:
        """
        Get all orphaned events that should be cleaned up.

        This includes:
        - Events for finished matches
        - Events for disabled tournaments
        - Events for deleted matches (will fail FK check)

        Args:
            organization_id: Organization ID for tenant scoping

        Returns:
            List of all DiscordScheduledEvent instances to clean up
        """
        # Get finished match events
        finished_events = await self.list_orphaned_events(organization_id)

        # Get events for disabled tournaments
        disabled_events = await self.list_events_for_disabled_tournaments(
            organization_id
        )

        # Combine and deduplicate
        all_event_ids = set()
        combined = []
        for event in finished_events + disabled_events:
            if event.id not in all_event_ids:
                all_event_ids.add(event.id)
                combined.append(event)

        logger.info(
            "Found %d total orphaned Discord events to clean up in org %s",
            len(combined),
            organization_id,
        )
        return combined
