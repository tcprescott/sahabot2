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
    from application.services.audit_service import AuditService
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
    from application.services.audit_service import AuditService
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
    from application.services.audit_service import AuditService
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
    from application.services.audit_service import AuditService
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
    from application.services.audit_service import AuditService
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
    from application.services.audit_service import AuditService
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
    from application.services.audit_service import AuditService
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
    from application.services.audit_service import AuditService
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
#     # TODO: Implement Discord notification
#     logger.info("TODO: Send tournament started notification")
#
# @EventBus.on(RaceApprovedEvent, priority=EventPriority.NORMAL)
# async def notify_race_approved(event: RaceApprovedEvent) -> None:
#     """Notify racer when their race is approved."""
#     # TODO: Implement user notification
#     logger.info("TODO: Send race approved notification")


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
#     # TODO: Implement statistics tracking
#     logger.info("TODO: Update race statistics")


logger.info("Event listeners registered")
