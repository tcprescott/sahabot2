"""
Event listeners for the application.

This module contains event handlers that respond to domain events.
Listeners are registered automatically when this module is imported.

Current listeners:
- Audit logging for all major events
- Future: Notification handlers, Discord announcements, etc.
"""

import logging
from application.events import EventBus, EventPriority
from application.events.types import (
    UserCreatedEvent,
    UserPermissionChangedEvent,
    OrganizationCreatedEvent,
    OrganizationMemberAddedEvent,
    OrganizationMemberRemovedEvent,
    TournamentCreatedEvent,
    RaceSubmittedEvent,
    RaceApprovedEvent,
    MatchScheduledEvent,
    MatchUpdatedEvent,
    MatchDeletedEvent,
    MatchCompletedEvent,
    TournamentMatchSettingsSubmittedEvent,
    InviteCreatedEvent,
    CrewAddedEvent,
    CrewApprovedEvent,
    CrewRemovedEvent,
    # Async Live Race events
    AsyncLiveRaceCreatedEvent,
    AsyncLiveRaceRoomOpenedEvent,
    AsyncLiveRaceStartedEvent,
    AsyncLiveRaceFinishedEvent,
    AsyncLiveRaceCancelledEvent,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Audit Logging Listeners
# ============================================================================
# These listeners create audit log entries for important events
# Priority: HIGH - audit logging should happen before other handlers

@EventBus.on(UserCreatedEvent, priority=EventPriority.HIGH)
async def log_user_created(event: UserCreatedEvent) -> None:
    """Log user creation to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who performed the action (may be system/None for self-registration)
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="user_created",
        details={
            "entity_id": event.entity_id,
            "discord_id": event.discord_id,
            "discord_username": event.discord_username,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged user creation: user_id=%s", event.entity_id)


@EventBus.on(UserPermissionChangedEvent, priority=EventPriority.HIGH)
async def log_user_permission_changed(event: UserPermissionChangedEvent) -> None:
    """Log user permission changes to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who performed the action
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="user_permission_changed",
        details={
            "entity_id": event.entity_id,
            "old_permission": event.old_permission,
            "new_permission": event.new_permission,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged permission change: user_id=%s, %s -> %s",
        event.entity_id,
        event.old_permission,
        event.new_permission
    )


@EventBus.on(OrganizationCreatedEvent, priority=EventPriority.HIGH)
async def log_organization_created(event: OrganizationCreatedEvent) -> None:
    """Log organization creation to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who created the organization
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="organization_created",
        details={
            "entity_id": event.entity_id,
            "organization_name": event.organization_name,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged organization creation: org_id=%s", event.entity_id)


@EventBus.on(OrganizationMemberAddedEvent, priority=EventPriority.HIGH)
async def log_organization_member_added(event: OrganizationMemberAddedEvent) -> None:
    """Log member addition to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who added the member
    user = await user_repo.get_by_id(event.added_by_user_id) if event.added_by_user_id else None

    await audit_service.log_action(
        user=user,
        action="organization_member_added",
        details={
            "member_user_id": event.member_user_id,
            "organization_id": event.organization_id,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged member addition: user_id=%s to org_id=%s",
        event.member_user_id,
        event.organization_id
    )


@EventBus.on(OrganizationMemberRemovedEvent, priority=EventPriority.HIGH)
async def log_organization_member_removed(event: OrganizationMemberRemovedEvent) -> None:
    """Log member removal to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who removed the member
    user = await user_repo.get_by_id(event.removed_by_user_id) if event.removed_by_user_id else None

    await audit_service.log_action(
        user=user,
        action="organization_member_removed",
        details={
            "member_user_id": event.member_user_id,
            "organization_id": event.organization_id,
            "reason": event.reason,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged member removal: user_id=%s from org_id=%s",
        event.member_user_id,
        event.organization_id
    )


@EventBus.on(TournamentCreatedEvent, priority=EventPriority.HIGH)
async def log_tournament_created(event: TournamentCreatedEvent) -> None:
    """Log tournament creation to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who created the tournament
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="tournament_created",
        details={
            "entity_id": event.entity_id,
            "tournament_name": event.tournament_name,
            "tournament_type": event.tournament_type,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged tournament creation: tournament_id=%s", event.entity_id)


@EventBus.on(RaceSubmittedEvent, priority=EventPriority.HIGH)
async def log_race_submitted(event: RaceSubmittedEvent) -> None:
    """Log race submission to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the racer who submitted
    user = await user_repo.get_by_id(event.racer_user_id) if event.racer_user_id else None

    await audit_service.log_action(
        user=user,
        action="race_submitted",
        details={
            "entity_id": event.entity_id,
            "tournament_id": event.tournament_id,
            "permalink_id": event.permalink_id,
            "time_seconds": event.time_seconds,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged race submission: race_id=%s, user_id=%s",
        event.entity_id,
        event.racer_user_id
    )


@EventBus.on(RaceApprovedEvent, priority=EventPriority.HIGH)
async def log_race_approved(event: RaceApprovedEvent) -> None:
    """Log race approval to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the reviewer who approved
    user = await user_repo.get_by_id(event.reviewer_user_id) if event.reviewer_user_id else None

    await audit_service.log_action(
        user=user,
        action="race_approved",
        details={
            "entity_id": event.entity_id,
            "tournament_id": event.tournament_id,
            "racer_user_id": event.racer_user_id,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged race approval: race_id=%s, reviewer_id=%s",
        event.entity_id,
        event.reviewer_user_id
    )


@EventBus.on(TournamentMatchSettingsSubmittedEvent, priority=EventPriority.HIGH)
async def log_match_settings_submitted(event: TournamentMatchSettingsSubmittedEvent) -> None:
    """Log tournament match settings submission to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who submitted
    user = await user_repo.get_by_id(event.submitted_by_user_id) if event.submitted_by_user_id else None

    await audit_service.log_action(
        user=user,
        action="tournament_match_settings_submitted",
        details={
            "entity_id": event.entity_id,
            "match_id": event.match_id,
            "tournament_id": event.tournament_id,
            "game_number": event.game_number,
            "settings": event.settings_data,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged settings submission: submission_id=%s, match_id=%s, user_id=%s",
        event.entity_id,
        event.match_id,
        event.submitted_by_user_id
    )


# ============================================================================
# Notification Listeners (Placeholder for future implementation)
# ============================================================================
# These will send notifications via Discord, email, etc.
# Priority: NORMAL - notifications happen after audit logging

# Example structure for future notification handlers:
#
# @EventBus.on(TournamentStartedEvent, priority=EventPriority.NORMAL)
# async def notify_tournament_started(event: TournamentStartedEvent) -> None:
#     """Send Discord notification when tournament starts."""
#     # Placeholder: implement Discord notification logic here
#     logger.info("Placeholder: Send tournament started notification")
#
# @EventBus.on(RaceApprovedEvent, priority=EventPriority.NORMAL)
# async def notify_race_approved(event: RaceApprovedEvent) -> None:
#     """Notify racer when their race is approved."""
#     # Placeholder: implement user notification logic here
#     logger.info("Placeholder: Send race approved notification")


# ============================================================================
# Statistics Listeners (Placeholder for future implementation)
# ============================================================================
# These will update statistics, analytics, etc.
# Priority: LOW - stats can be updated last

# Example structure for future stats handlers:
#
# @EventBus.on(RaceSubmittedEvent, priority=EventPriority.LOW)
# async def update_race_statistics(event: RaceSubmittedEvent) -> None:
#     """Update tournament statistics when race is submitted."""
#     # Placeholder: implement statistics tracking logic here
#     logger.info("Placeholder: Update race statistics")


# ============================================================================
# Notification Listeners
# ============================================================================
# These listeners queue notifications for subscribed users
# Priority: NORMAL - notifications happen after audit logging

@EventBus.on(MatchScheduledEvent, priority=EventPriority.NORMAL)
async def notify_match_scheduled(event: MatchScheduledEvent) -> None:
    """Queue notifications for match scheduled event."""
    from application.services.notifications.notification_service import NotificationService
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get all participants
    participant_ids = event.participant_ids or []
    if not participant_ids:
        logger.debug("No participants for match %s, skipping notifications", event.entity_id)
        return

    # Fetch all participant users
    participants = []
    for participant_id in participant_ids:
        user = await user_repo.get_by_id(participant_id)
        if user:
            participants.append(user)

    if not participants:
        logger.warning("Could not find any participant users for match %s", event.entity_id)
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
        logger.debug("Queued match scheduled notification for participant %s", participant.id)


@EventBus.on(TournamentMatchSettingsSubmittedEvent, priority=EventPriority.NORMAL)
async def notify_match_settings_submitted(event: TournamentMatchSettingsSubmittedEvent) -> None:
    """Queue notifications for match settings submission."""
    from application.services.notifications.notification_service import NotificationService
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType
    from models.match_schedule import MatchPlayers

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get all participants in the match
    participants = await MatchPlayers.filter(match_id=event.match_id).prefetch_related('user')
    if not participants:
        logger.debug("No participants for match %s, skipping notifications", event.match_id)
        return

    # Get the submitter
    submitter = await user_repo.get_by_id(event.submitted_by_user_id) if event.submitted_by_user_id else None
    submitter_name = submitter.get_display_name() if submitter else "Unknown"

    # Base event data
    base_event_data = {
        "match_id": event.match_id,
        "tournament_id": event.tournament_id,
        "game_number": event.game_number,
        "submitted_by": submitter_name,
        "submitted_by_id": event.submitted_by_user_id,
        "settings_summary": _format_settings_summary(event.settings_data) if event.settings_data else "Settings submitted",
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
            event.match_id
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


@EventBus.on(TournamentCreatedEvent, priority=EventPriority.NORMAL)
async def notify_tournament_created(event: TournamentCreatedEvent) -> None:
    """Queue notifications for tournament created event."""
    from application.services.notifications.notification_service import NotificationService
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
        "Queued tournament created notifications for tournament %s",
        event.entity_id
    )


@EventBus.on(InviteCreatedEvent, priority=EventPriority.NORMAL)
async def notify_invite_created(event: InviteCreatedEvent) -> None:
    """Queue notifications for organization invite event."""
    from application.services.notifications.notification_service import NotificationService
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the invited user
    invited_user = await user_repo.get_by_id(event.invited_user_id) if event.invited_user_id else None
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


@EventBus.on(CrewAddedEvent, priority=EventPriority.NORMAL)
async def notify_crew_added_auto_approved(event: CrewAddedEvent) -> None:
    """Queue notifications when crew is added in auto-approved state (admin added)."""
    from application.services.notifications.notification_service import NotificationService
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType
    from models.match_schedule import Match

    # Only notify if auto-approved (admin added them directly)
    if not event.auto_approved:
        return

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the crew member user
    crew_user = await user_repo.get_by_id(event.crew_user_id) if event.crew_user_id else None
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
        match = await Match.filter(id=event.match_id).prefetch_related(
            'tournament',
            'stream_channel',
            'players__user'
        ).first()
        
        if match:
            # Get tournament name
            if match.tournament:
                tournament_name = match.tournament.name
            
            # Get stream channel name
            if match.stream_channel:
                stream_channel = match.stream_channel.name
            
            # Get player names
            if match.players:
                player_names = [p.user.get_display_name() for p in match.players if p.user]

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
    from application.services.notifications.notification_service import NotificationService
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType
    from models.match_schedule import Match

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the crew member user
    crew_user = await user_repo.get_by_id(event.crew_user_id) if event.crew_user_id else None
    if not crew_user:
        logger.warning("Could not find crew user %s", event.crew_user_id)
        return

    # Get the approver
    approved_by = await user_repo.get_by_id(event.approved_by_user_id) if event.approved_by_user_id else None

    # Get match details
    match = None
    tournament_name = None
    stream_channel = None
    player_names = []
    
    if event.match_id:
        match = await Match.filter(id=event.match_id).prefetch_related(
            'tournament',
            'stream_channel',
            'players__user'
        ).first()
        
        if match:
            # Get tournament name
            if match.tournament:
                tournament_name = match.tournament.name
            
            # Get stream channel name
            if match.stream_channel:
                stream_channel = match.stream_channel.name
            
            # Get player names
            if match.players:
                player_names = [p.user.get_display_name() for p in match.players if p.user]

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
    from application.services.notifications.notification_service import NotificationService
    from application.repositories.user_repository import UserRepository
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    user_repo = UserRepository()

    # Get the crew member user
    crew_user = await user_repo.get_by_id(event.crew_user_id) if event.crew_user_id else None
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
# These listeners queue notifications for live race events
# Priority: NORMAL - notifications happen after audit logging

@EventBus.on(AsyncLiveRaceCreatedEvent, priority=EventPriority.NORMAL)
async def notify_live_race_scheduled(event: AsyncLiveRaceCreatedEvent) -> None:
    """Queue notifications when a live race is scheduled."""
    from application.services.notifications.notification_service import NotificationService
    from application.services.tournaments.async_live_race_service import AsyncLiveRaceService
    from models.notification_subscription import NotificationEventType

    notification_service = NotificationService()
    live_race_service = AsyncLiveRaceService()

    # Get eligible participants for this race
    try:
        eligibility_list = await live_race_service.get_eligible_participants(
            organization_id=event.organization_id,
            live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning("Could not get eligible participants for live race %s: %s", event.entity_id, e)
        return

    # Filter to only eligible participants
    eligible_users = [e.user for e in eligibility_list if e.is_eligible]
    if not eligible_users:
        logger.debug("No eligible participants for live race %s, skipping notifications", event.entity_id)
        return

    # Base event data
    event_data = {
        "live_race_id": event.entity_id,
        "tournament_id": event.tournament_id,
        "tournament_name": event.tournament_name,
        "pool_name": event.pool_name,
        "scheduled_time": event.scheduled_time.isoformat() if event.scheduled_time else None,
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
    from application.services.notifications.notification_service import NotificationService
    from application.services.tournaments.async_live_race_service import AsyncLiveRaceService
    from application.repositories.async_live_race_repository import AsyncLiveRaceRepository
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
            organization_id=event.organization_id,
            live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning("Could not get eligible participants for live race %s: %s", event.entity_id, e)
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
        "tournament_name": live_race.tournament.name if live_race.tournament else "Unknown",
        "pool_name": live_race.pool_name,
        "racetime_url": event.racetime_url,
        "scheduled_time": live_race.scheduled_time.isoformat() if live_race.scheduled_time else None,
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
    from application.services.notifications.notification_service import NotificationService
    from application.services.tournaments.async_live_race_service import AsyncLiveRaceService
    from application.repositories.async_live_race_repository import AsyncLiveRaceRepository
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
            organization_id=event.organization_id,
            live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning("Could not get eligible participants for live race %s: %s", event.entity_id, e)
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
        "tournament_name": live_race.tournament.name if live_race.tournament else "Unknown",
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
    from application.services.notifications.notification_service import NotificationService
    from application.services.tournaments.async_live_race_service import AsyncLiveRaceService
    from application.repositories.async_live_race_repository import AsyncLiveRaceRepository
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
            organization_id=event.organization_id,
            live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning("Could not get eligible participants for live race %s: %s", event.entity_id, e)
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
        "tournament_name": live_race.tournament.name if live_race.tournament else "Unknown",
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
    from application.services.notifications.notification_service import NotificationService
    from application.services.tournaments.async_live_race_service import AsyncLiveRaceService
    from application.repositories.async_live_race_repository import AsyncLiveRaceRepository
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
            organization_id=event.organization_id,
            live_race_id=event.entity_id
        )
    except ValueError as e:
        logger.warning("Could not get eligible participants for live race %s: %s", event.entity_id, e)
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
        "tournament_name": live_race.tournament.name if live_race.tournament else "Unknown",
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


# ============================================================================
# Discord Scheduled Events Listeners
# ============================================================================
# These listeners manage Discord scheduled events for tournament matches
# Priority: NORMAL - runs after audit logging

@EventBus.on(MatchScheduledEvent, priority=EventPriority.NORMAL)
async def create_discord_event_for_match(event: MatchScheduledEvent) -> None:
    """Create Discord scheduled event when a match is scheduled."""
    from application.services.discord.discord_scheduled_event_service import DiscordScheduledEventService

    service = DiscordScheduledEventService()
    
    try:
        await service.create_event_for_match(
            user_id=event.user_id,
            organization_id=event.organization_id,
            match_id=event.entity_id,
        )
        logger.debug("Created Discord event for match %s", event.entity_id)
    except Exception as e:
        logger.exception("Failed to create Discord event for match %s: %s", event.entity_id, e)


@EventBus.on(MatchUpdatedEvent, priority=EventPriority.NORMAL)
async def update_discord_event_for_match(event: MatchUpdatedEvent) -> None:
    """Update Discord scheduled event when match details change."""
    from application.services.discord.discord_scheduled_event_service import DiscordScheduledEventService

    # Only update Discord event if relevant fields changed
    relevant_fields = {'scheduled_at', 'title', 'stream_channel_id', 'comment'}
    changed_fields = set(event.changed_fields or [])
    
    if not changed_fields.intersection(relevant_fields):
        logger.debug("Match %s updated but no relevant fields changed, skipping Discord event update", event.entity_id)
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
        logger.exception("Failed to update Discord event for match %s: %s", event.entity_id, e)


@EventBus.on(MatchDeletedEvent, priority=EventPriority.NORMAL)
async def delete_discord_event_for_match(event: MatchDeletedEvent) -> None:
    """Delete Discord scheduled event when a match is deleted."""
    from application.services.discord.discord_scheduled_event_service import DiscordScheduledEventService

    service = DiscordScheduledEventService()
    
    try:
        await service.delete_event_for_match(
            user_id=event.user_id,
            organization_id=event.organization_id,
            match_id=event.entity_id,
        )
        logger.debug("Deleted Discord event for match %s", event.entity_id)
    except Exception as e:
        logger.exception("Failed to delete Discord event for match %s: %s", event.entity_id, e)


@EventBus.on(MatchCompletedEvent, priority=EventPriority.NORMAL)
async def cleanup_discord_event_for_completed_match(event: MatchCompletedEvent) -> None:
    """Clean up Discord scheduled event when a match is completed."""
    from application.services.discord.discord_scheduled_event_service import DiscordScheduledEventService

    service = DiscordScheduledEventService()
    
    try:
        await service.delete_event_for_match(
            user_id=event.user_id,
            organization_id=event.organization_id,
            match_id=event.entity_id,
        )
        logger.debug("Cleaned up Discord event for completed match %s", event.entity_id)
    except Exception as e:
        logger.exception("Failed to clean up Discord event for match %s: %s", event.entity_id, e)


logger.info("Event listeners registered")
