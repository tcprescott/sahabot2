"""
Tournament domain event listeners.

Handles audit logging for tournament lifecycle events.
"""

import logging
from application.events import EventBus, EventPriority
from application.events.types import (
    TournamentCreatedEvent,
    TournamentUpdatedEvent,
    TournamentDeletedEvent,
    TournamentStartedEvent,
    TournamentEndedEvent,
)

logger = logging.getLogger(__name__)


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


@EventBus.on(TournamentUpdatedEvent, priority=EventPriority.HIGH)
async def log_tournament_updated(event: TournamentUpdatedEvent) -> None:
    """Log tournament update to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who updated the tournament
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="tournament_updated",
        details={
            "entity_id": event.entity_id,
            "changed_fields": event.changed_fields,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged tournament update: tournament_id=%s", event.entity_id)


@EventBus.on(TournamentDeletedEvent, priority=EventPriority.HIGH)
async def log_tournament_deleted(event: TournamentDeletedEvent) -> None:
    """Log tournament deletion to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who deleted the tournament
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="tournament_deleted",
        details={
            "entity_id": event.entity_id,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged tournament deletion: tournament_id=%s", event.entity_id)


@EventBus.on(TournamentStartedEvent, priority=EventPriority.HIGH)
async def log_tournament_started(event: TournamentStartedEvent) -> None:
    """Log tournament start to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who started the tournament
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="tournament_started",
        details={
            "entity_id": event.entity_id,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged tournament start: tournament_id=%s", event.entity_id)


@EventBus.on(TournamentEndedEvent, priority=EventPriority.HIGH)
async def log_tournament_ended(event: TournamentEndedEvent) -> None:
    """Log tournament end to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who ended the tournament
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="tournament_ended",
        details={
            "entity_id": event.entity_id,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged tournament end: tournament_id=%s", event.entity_id)


logger.debug("Tournament event listeners registered")
