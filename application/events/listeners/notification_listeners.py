"""
Notification domain event listeners.

Handles queuing notifications for various events including matches, tournaments,
invites, crew management, and async live races.
Priority: NORMAL - notifications happen after audit logging.
"""

import logging
from application.events import EventBus, EventPriority
from application.events.types import (
    MatchScheduledEvent,
    TournamentMatchSettingsSubmittedEvent,
    TournamentCreatedEvent,
    InviteCreatedEvent,
    CrewAddedEvent,
    CrewApprovedEvent,
    CrewRemovedEvent,
    # Async Live Race events
    AsyncLiveRaceCreatedEvent,
    AsyncLiveRaceUpdatedEvent,
    AsyncLiveRaceRoomOpenedEvent,
    AsyncLiveRaceStartedEvent,
    AsyncLiveRaceFinishedEvent,
    AsyncLiveRaceCancelledEvent,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Match Notification Listeners
# ============================================================================


@EventBus.on(MatchScheduledEvent, priority=EventPriority.NORMAL)
async def notify_match_scheduled(event: MatchScheduledEvent) -> None:
    """Queue notifications for match scheduled event."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get all participants
    participant_ids = event.participant_ids or []
    if not participant_ids:
        logger.debug(
            "No participants for match %s, skipping notifications", event.entity_id
        )
        return

    # Fetch all participant users
    participants = []
    for participant_id in participant_ids:
        user = await user_repo.get_by_id(participant_id)
        if user:
            participants.append(user)

    if not participants:
        logger.warning(
            "Could not find any participant users for match %s", event.entity_id
        )
        return

    # Base event data (common to all notifications)
    base_event_data = {
        "scheduled_time": event.scheduled_time if event.scheduled_time else None,
        "match_id": event.entity_id,
        "tournament_id": event.tournament_id,
        "participant_count": len(participants),
    }

    # Notify each participant
    for participant in participants:
        # Get opponent names (all other participants)
        opponent_names = [
            p.get_display_name() for p in participants if p.id != participant.id
        ]

        await notification_service.queue_notification(
            user=participant,
            event_type=NotificationEventType.MATCH_SCHEDULED,
            event_data={
                **base_event_data,
                "opponents": opponent_names,
            },
            organization_id=event.organization_id,
        )
        logger.debug(
            "Queued match scheduled notification for participant %s", participant.id
        )


@EventBus.on(TournamentMatchSettingsSubmittedEvent, priority=EventPriority.NORMAL)
async def notify_match_settings_submitted(
    event: TournamentMatchSettingsSubmittedEvent,
) -> None:
    """Queue notifications for match settings submission."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType
    from models.match_schedule import MatchPlayers

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get all participants in the match
    participants = await MatchPlayers.filter(match_id=event.match_id).prefetch_related(
        "user"
    )
    if not participants:
        logger.debug(
            "No participants for match %s, skipping notifications", event.match_id
        )
        return

    # Get the submitter
    submitter = (
        await user_repo.get_by_id(event.submitted_by_user_id)
        if event.submitted_by_user_id
        else None
    )
    submitter_name = submitter.get_display_name() if submitter else "Unknown"

    # Base event data
    base_event_data = {
        "match_id": event.match_id,
        "tournament_id": event.tournament_id,
        "game_number": event.game_number,
        "submitted_by": submitter_name,
        "submitted_by_id": event.submitted_by_user_id,
        "settings_summary": (
            _format_settings_summary(event.settings_data)
            if event.settings_data
            else "Settings submitted"
        ),
        "submission_url": f"/tournaments/matches/{event.match_id}/submit",
    }

    # Notify all participants except the submitter
    for participant in participants:
        if participant.user_id == event.submitted_by_user_id:
            # Skip notifying the submitter themselves
            continue

        await notification_service.queue_notification(
            user=participant.user,
            event_type=NotificationEventType.MATCH_SETTINGS_SUBMITTED,
            event_data=base_event_data,
            organization_id=event.organization_id,
        )
        logger.debug(
            "Queued match settings notification for participant %s (match %s)",
            participant.user_id,
            event.match_id,
        )


def _format_settings_summary(settings: dict) -> str:
    """
    Format settings dict into a readable summary.

    Args:
        settings: Settings dictionary

    Returns:
        Formatted summary string
    """
    if not settings:
        return "Settings submitted"

    # Try to extract common fields
    parts = []

    if "preset" in settings:
        parts.append(f"Preset: {settings['preset']}")

    if "mode" in settings:
        parts.append(f"Mode: {settings['mode']}")

    if "difficulty" in settings:
        parts.append(f"Difficulty: {settings['difficulty']}")

    # If no common fields, show a count
    if not parts:
        parts.append(f"{len(settings)} settings configured")

    return ", ".join(parts)


# ============================================================================
# Tournament Notification Listeners
# ============================================================================


@EventBus.on(TournamentCreatedEvent, priority=EventPriority.NORMAL)
async def notify_tournament_created(event: TournamentCreatedEvent) -> None:
    """Queue notifications for tournament created event."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()

    event_data = {
        "tournament_name": event.tournament_name,
        "tournament_id": event.entity_id,
        "format": event.tournament_format,
        "start_date": event.start_date.isoformat() if event.start_date else None,
    }

    # This will queue notifications for ALL users subscribed to tournament creation
    # The notification service will find all subscribed users and create notification logs
    # Note: We pass None for user since this is a broadcast notification
    # The service handles finding all subscribed users
    await notification_service.queue_broadcast_notification(
        event_type=NotificationEventType.TOURNAMENT_CREATED,
        event_data=event_data,
        organization_id=event.organization_id,
    )
    logger.debug(
        "Queued tournament created notifications for tournament %s", event.entity_id
    )


# ============================================================================
# Invite Notification Listeners
# ============================================================================


@EventBus.on(InviteCreatedEvent, priority=EventPriority.NORMAL)
async def notify_invite_created(event: InviteCreatedEvent) -> None:
    """Queue notifications for organization invite event."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the invited user
    invited_user = (
        await user_repo.get_by_id(event.invited_user_id)
        if event.invited_user_id
        else None
    )
    if not invited_user:
        logger.warning("Could not find invited user %s", event.invited_user_id)
        return

    # Get the inviter
    inviter = await user_repo.get_by_id(event.user_id) if event.user_id else None

    event_data = {
        "organization_name": event.organization_name,
        "organization_id": event.organization_id,
        "invite_id": event.entity_id,
        "invited_by": inviter.get_display_name() if inviter else "Unknown",
    }

    await notification_service.queue_notification(
        user=invited_user,
        event_type=NotificationEventType.INVITE_RECEIVED,
        event_data=event_data,
        organization_id=event.organization_id,
    )
    logger.debug("Queued invite notification for user %s", invited_user.id)


# ============================================================================
# Crew Notification Listeners
# ============================================================================


@EventBus.on(CrewAddedEvent, priority=EventPriority.NORMAL)
async def notify_crew_added_auto_approved(event: CrewAddedEvent) -> None:
    """Queue notifications when crew is added in auto-approved state (admin added)."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType
    from models.match_schedule import Match

    # Only notify if auto-approved (admin added them directly)
    if not event.auto_approved:
        return

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the crew member user
    crew_user = (
        await user_repo.get_by_id(event.crew_user_id) if event.crew_user_id else None
    )
    if not crew_user:
        logger.warning("Could not find crew user %s", event.crew_user_id)
        return

    # Get the admin who added them
    added_by = await user_repo.get_by_id(event.user_id) if event.user_id else None

    # Get match details
    match = None
    tournament_name = None
    stream_channel = None
    player_names = []

    if event.match_id:
        match = (
            await Match.filter(id=event.match_id)
            .prefetch_related("tournament", "stream_channel", "players__user")
            .first()
        )

        if match:
            # Get tournament name
            if match.tournament:
                tournament_name = match.tournament.name

            # Get stream channel name
            if match.stream_channel:
                stream_channel = match.stream_channel.name

            # Get player names
            if match.players:
                player_names = [
                    p.user.get_display_name() for p in match.players if p.user
                ]

    event_data = {
        "match_id": event.match_id,
        "crew_id": event.entity_id,
        "role": event.role,
        "added_by": added_by.get_display_name() if added_by else "Admin",
        "auto_approved": True,
        "tournament_name": tournament_name,
        "stream_channel": stream_channel,
        "players": player_names,
    }

    await notification_service.queue_notification(
        user=crew_user,
        event_type=NotificationEventType.CREW_APPROVED,
        event_data=event_data,
        organization_id=event.organization_id,
    )
    logger.debug("Queued crew auto-approved notification for user %s", crew_user.id)


@EventBus.on(CrewApprovedEvent, priority=EventPriority.NORMAL)
async def notify_crew_approved(event: CrewApprovedEvent) -> None:
    """Queue notifications when crew signup is approved."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType
    from models.match_schedule import Match

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the crew member user
    crew_user = (
        await user_repo.get_by_id(event.crew_user_id) if event.crew_user_id else None
    )
    if not crew_user:
        logger.warning("Could not find crew user %s", event.crew_user_id)
        return

    # Get the approver
    approved_by = (
        await user_repo.get_by_id(event.approved_by_user_id)
        if event.approved_by_user_id
        else None
    )

    # Get match details
    match = None
    tournament_name = None
    stream_channel = None
    player_names = []

    if event.match_id:
        match = (
            await Match.filter(id=event.match_id)
            .prefetch_related("tournament", "stream_channel", "players__user")
            .first()
        )

        if match:
            # Get tournament name
            if match.tournament:
                tournament_name = match.tournament.name

            # Get stream channel name
            if match.stream_channel:
                stream_channel = match.stream_channel.name

            # Get player names
            if match.players:
                player_names = [
                    p.user.get_display_name() for p in match.players if p.user
                ]

    event_data = {
        "match_id": event.match_id,
        "crew_id": event.entity_id,
        "role": event.role,
        "approved_by": approved_by.get_display_name() if approved_by else "Admin",
        "auto_approved": False,
        "tournament_name": tournament_name,
        "stream_channel": stream_channel,
        "players": player_names,
    }

    await notification_service.queue_notification(
        user=crew_user,
        event_type=NotificationEventType.CREW_APPROVED,
        event_data=event_data,
        organization_id=event.organization_id,
    )
    logger.debug("Queued crew approved notification for user %s", crew_user.id)


@EventBus.on(CrewRemovedEvent, priority=EventPriority.NORMAL)
async def notify_crew_removed(event: CrewRemovedEvent) -> None:
    """Queue notifications when crew is removed from a match."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the crew member user
    crew_user = (
        await user_repo.get_by_id(event.crew_user_id) if event.crew_user_id else None
    )
    if not crew_user:
        logger.warning("Could not find crew user %s", event.crew_user_id)
        return

    event_data = {
        "match_id": event.match_id,
        "crew_id": event.entity_id,
        "role": event.role,
    }

    await notification_service.queue_notification(
        user=crew_user,
        event_type=NotificationEventType.CREW_REMOVED,
        event_data=event_data,
        organization_id=event.organization_id,
    )
    logger.debug("Queued crew removed notification for user %s", crew_user.id)


# ============================================================================
# Async Live Race Notification Listeners
# ============================================================================


@EventBus.on(AsyncLiveRaceCreatedEvent, priority=EventPriority.NORMAL)
async def notify_live_race_scheduled(event: AsyncLiveRaceCreatedEvent) -> None:
    """Queue notifications when a live race is scheduled."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from plugins.builtin.async_qualifier.services import (
        AsyncLiveRaceService,
    )
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    live_race_service = AsyncLiveRaceService()

    # Get eligible participants for this race
    try:
        eligibility_list = await live_race_service.get_eligible_participants(
            organization_id=event.organization_id, live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning(
            "Could not get eligible participants for live race %s: %s",
            event.entity_id,
            e,
        )
        return

    # Filter to only eligible participants
    eligible_users = [e.user for e in eligibility_list if e.is_eligible]
    if not eligible_users:
        logger.debug(
            "No eligible participants for live race %s, skipping notifications",
            event.entity_id,
        )
        return

    # Base event data
    event_data = {
        "live_race_id": event.entity_id,
        "tournament_id": event.tournament_id,
        "tournament_name": event.tournament_name,
        "pool_name": event.pool_name,
        "scheduled_time": (
            event.scheduled_time.isoformat() if event.scheduled_time else None
        ),
    }

    # Notify each eligible participant
    for user in eligible_users:
        await notification_service.queue_notification(
            user=user,
            event_type=NotificationEventType.LIVE_RACE_SCHEDULED,
            event_data=event_data,
            organization_id=event.organization_id,
        )
        logger.debug("Queued live race scheduled notification for user %s", user.id)


@EventBus.on(AsyncLiveRaceRoomOpenedEvent, priority=EventPriority.NORMAL)
async def notify_live_race_room_opened(event: AsyncLiveRaceRoomOpenedEvent) -> None:
    """Queue notifications when a live race room opens."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from plugins.builtin.async_qualifier.services import (
        AsyncLiveRaceService,
    )
    from plugins.builtin.async_qualifier.repositories import (
        AsyncLiveRaceRepository,
    )
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    live_race_service = AsyncLiveRaceService()
    live_race_repo = AsyncLiveRaceRepository()

    # Get the live race
    live_race = await live_race_repo.get_by_id_with_relations(event.entity_id)
    if not live_race:
        logger.warning("Could not find live race %s", event.entity_id)
        return

    # Get eligible participants
    try:
        eligibility_list = await live_race_service.get_eligible_participants(
            organization_id=event.organization_id, live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning(
            "Could not get eligible participants for live race %s: %s",
            event.entity_id,
            e,
        )
        return

    # Filter to only eligible participants
    eligible_users = [e.user for e in eligibility_list if e.is_eligible]
    if not eligible_users:
        logger.debug("No eligible participants for live race %s", event.entity_id)
        return

    # Base event data
    event_data = {
        "live_race_id": event.entity_id,
        "tournament_id": live_race.tournament_id,
        "tournament_name": (
            live_race.tournament.name if live_race.tournament else "Unknown"
        ),
        "pool_name": live_race.pool_name,
        "racetime_url": event.racetime_url,
        "scheduled_time": (
            live_race.scheduled_time.isoformat() if live_race.scheduled_time else None
        ),
    }

    # Notify each eligible participant
    for user in eligible_users:
        await notification_service.queue_notification(
            user=user,
            event_type=NotificationEventType.LIVE_RACE_ROOM_OPENED,
            event_data=event_data,
            organization_id=event.organization_id,
        )
        logger.debug("Queued live race room opened notification for user %s", user.id)


@EventBus.on(AsyncLiveRaceStartedEvent, priority=EventPriority.NORMAL)
async def notify_live_race_started(event: AsyncLiveRaceStartedEvent) -> None:
    """Queue notifications when a live race starts."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from plugins.builtin.async_qualifier.services import (
        AsyncLiveRaceService,
    )
    from plugins.builtin.async_qualifier.repositories import (
        AsyncLiveRaceRepository,
    )
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    live_race_service = AsyncLiveRaceService()
    live_race_repo = AsyncLiveRaceRepository()

    # Get the live race
    live_race = await live_race_repo.get_by_id_with_relations(event.entity_id)
    if not live_race:
        logger.warning("Could not find live race %s", event.entity_id)
        return

    # Get eligible participants
    try:
        eligibility_list = await live_race_service.get_eligible_participants(
            organization_id=event.organization_id, live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning(
            "Could not get eligible participants for live race %s: %s",
            event.entity_id,
            e,
        )
        return

    # Filter to only eligible participants
    eligible_users = [e.user for e in eligibility_list if e.is_eligible]
    if not eligible_users:
        logger.debug("No eligible participants for live race %s", event.entity_id)
        return

    # Base event data
    event_data = {
        "live_race_id": event.entity_id,
        "tournament_id": live_race.tournament_id,
        "tournament_name": (
            live_race.tournament.name if live_race.tournament else "Unknown"
        ),
        "pool_name": live_race.pool_name,
        "participant_count": event.participant_count,
        "racetime_url": live_race.racetime_url,
    }

    # Notify each eligible participant
    for user in eligible_users:
        await notification_service.queue_notification(
            user=user,
            event_type=NotificationEventType.LIVE_RACE_STARTED,
            event_data=event_data,
            organization_id=event.organization_id,
        )
        logger.debug("Queued live race started notification for user %s", user.id)


@EventBus.on(AsyncLiveRaceFinishedEvent, priority=EventPriority.NORMAL)
async def notify_live_race_finished(event: AsyncLiveRaceFinishedEvent) -> None:
    """Queue notifications when a live race finishes."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from plugins.builtin.async_qualifier.services import (
        AsyncLiveRaceService,
    )
    from plugins.builtin.async_qualifier.repositories import (
        AsyncLiveRaceRepository,
    )
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    live_race_service = AsyncLiveRaceService()
    live_race_repo = AsyncLiveRaceRepository()

    # Get the live race
    live_race = await live_race_repo.get_by_id_with_relations(event.entity_id)
    if not live_race:
        logger.warning("Could not find live race %s", event.entity_id)
        return

    # Get eligible participants
    try:
        eligibility_list = await live_race_service.get_eligible_participants(
            organization_id=event.organization_id, live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning(
            "Could not get eligible participants for live race %s: %s",
            event.entity_id,
            e,
        )
        return

    # Filter to only eligible participants
    eligible_users = [e.user for e in eligibility_list if e.is_eligible]
    if not eligible_users:
        logger.debug("No eligible participants for live race %s", event.entity_id)
        return

    # Base event data
    event_data = {
        "live_race_id": event.entity_id,
        "tournament_id": live_race.tournament_id,
        "tournament_name": (
            live_race.tournament.name if live_race.tournament else "Unknown"
        ),
        "pool_name": live_race.pool_name,
        "finisher_count": event.finisher_count,
        "racetime_url": live_race.racetime_url,
    }

    # Notify each eligible participant
    for user in eligible_users:
        await notification_service.queue_notification(
            user=user,
            event_type=NotificationEventType.LIVE_RACE_FINISHED,
            event_data=event_data,
            organization_id=event.organization_id,
        )
        logger.debug("Queued live race finished notification for user %s", user.id)


@EventBus.on(AsyncLiveRaceCancelledEvent, priority=EventPriority.NORMAL)
async def notify_live_race_cancelled(event: AsyncLiveRaceCancelledEvent) -> None:
    """Queue notifications when a live race is cancelled."""
    from application.services.notifications.notification_service import (
        NotificationService,
    )
    from plugins.builtin.async_qualifier.services import (
        AsyncLiveRaceService,
    )
    from plugins.builtin.async_qualifier.repositories import (
        AsyncLiveRaceRepository,
    )
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    live_race_service = AsyncLiveRaceService()
    live_race_repo = AsyncLiveRaceRepository()

    # Get the live race
    live_race = await live_race_repo.get_by_id_with_relations(event.entity_id)
    if not live_race:
        logger.warning("Could not find live race %s", event.entity_id)
        return

    # Get eligible participants
    try:
        eligibility_list = await live_race_service.get_eligible_participants(
            organization_id=event.organization_id, live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning(
            "Could not get eligible participants for live race %s: %s",
            event.entity_id,
            e,
        )
        return

    # Filter to only eligible participants
    eligible_users = [e.user for e in eligibility_list if e.is_eligible]
    if not eligible_users:
        logger.debug("No eligible participants for live race %s", event.entity_id)
        return

    # Base event data
    event_data = {
        "live_race_id": event.entity_id,
        "tournament_id": live_race.tournament_id,
        "tournament_name": (
            live_race.tournament.name if live_race.tournament else "Unknown"
        ),
        "pool_name": live_race.pool_name,
        "reason": event.reason,
    }

    # Notify each eligible participant
    for user in eligible_users:
        await notification_service.queue_notification(
            user=user,
            event_type=NotificationEventType.LIVE_RACE_CANCELLED,
            event_data=event_data,
            organization_id=event.organization_id,
        )
        logger.debug("Queued live race cancelled notification for user %s", user.id)


@EventBus.on(AsyncLiveRaceUpdatedEvent, priority=EventPriority.HIGH)
async def log_async_live_race_updated(event: AsyncLiveRaceUpdatedEvent) -> None:
    """Log async live race update to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who updated the live race
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="async_live_race_updated",
        details={
            "entity_id": event.entity_id,
            "tournament_id": event.tournament_id,
            "changed_fields": event.changed_fields,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged async live race update: live_race_id=%s", event.entity_id)


logger.debug("Notification event listeners registered")
