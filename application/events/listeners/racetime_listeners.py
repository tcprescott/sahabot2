"""
RaceTime domain event listeners.

Handles auto-advancing match status based on RaceTime room and race status changes.
Priority: NORMAL - runs after audit logging.
"""

import logging
from datetime import datetime, timezone
from application.events import (
    EventBus,
    EventPriority,
    RacetimeRoomOpenedEvent,
    RacetimeRaceStatusChangedEvent,
    MatchFinishedEvent,
)
from models import Match
from models.racetime_room import RacetimeRoom

logger = logging.getLogger(__name__)


@EventBus.on(RacetimeRoomOpenedEvent, priority=EventPriority.NORMAL)
async def advance_match_on_room_opened(event: RacetimeRoomOpenedEvent) -> None:
    """Advance match to 'checked_in' status when RaceTime room is opened."""
    if not event.match_id:
        return

    try:
        # Get the match
        match = await Match.filter(id=event.match_id).first()
        if not match:
            logger.warning(
                "Match %s not found for RacetimeRoomOpenedEvent", event.match_id
            )
            return

        # Only advance if not already checked in
        if not match.checked_in_at:
            match.checked_in_at = datetime.now(timezone.utc)
            await match.save()
            logger.info(
                "Auto-advanced match %s to 'checked_in' status (room opened)",
                event.match_id,
            )
        else:
            logger.debug(
                "Match %s already checked in, skipping auto-advance", event.match_id
            )

    except Exception as e:
        logger.exception(
            "Failed to auto-advance match %s on room opened: %s", event.match_id, e
        )


@EventBus.on(RacetimeRaceStatusChangedEvent, priority=EventPriority.NORMAL)
async def advance_match_on_race_status_changed(
    event: RacetimeRaceStatusChangedEvent,
) -> None:
    """Advance match status when RaceTime race status changes."""
    if not event.match_id:
        return

    try:
        # Get the match
        match = await Match.filter(id=event.match_id).first()
        if not match:
            logger.debug(
                "Match %s not found for RacetimeRaceStatusChangedEvent", event.match_id
            )
            return

        # Advance based on race status
        now = datetime.now(timezone.utc)

        if event.new_status == "in_progress":
            # Race started - advance to 'started'
            if not match.started_at:
                match.started_at = now
                await match.save()
                logger.info(
                    "Auto-advanced match %s to 'started' status (race in progress)",
                    event.match_id,
                )
            else:
                logger.debug(
                    "Match %s already started, skipping auto-advance", event.match_id
                )

        elif event.new_status == "finished":
            # Race finished - advance to 'finished'
            if not match.finished_at:
                match.finished_at = now
                await match.save()
                logger.info(
                    "Auto-advanced match %s to 'finished' status (race finished)",
                    event.match_id,
                )

                # Emit MatchFinishedEvent
                await EventBus.emit(
                    MatchFinishedEvent(
                        user_id=event.user_id,
                        organization_id=event.organization_id,
                        entity_id=event.match_id,
                        match_id=event.match_id,
                        tournament_id=event.tournament_id,
                    )
                )
                logger.info(
                    "Emitted MatchFinishedEvent for match %s (auto-advanced)",
                    event.match_id,
                )
            else:
                logger.debug(
                    "Match %s already finished, skipping auto-advance", event.match_id
                )

        elif event.new_status == "cancelled":
            # Race cancelled - unlink RaceTime room from match
            room = await RacetimeRoom.filter(
                slug=event.room_slug, match_id=event.match_id
            ).first()
            if room:
                await room.delete()
                logger.info(
                    "Auto-unlinked RaceTime room %s from match %s (race cancelled)",
                    event.room_slug,
                    event.match_id,
                )
            else:
                logger.debug(
                    "No RaceTime room found for match %s to unlink (race cancelled)",
                    event.match_id,
                )

    except Exception as e:
        logger.exception(
            "Failed to auto-advance match %s on race status change: %s",
            event.match_id,
            e,
        )


logger.debug("RaceTime event listeners registered")
