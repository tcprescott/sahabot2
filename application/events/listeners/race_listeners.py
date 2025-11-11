"""
Race domain event listeners.

Handles audit logging for race submissions, approvals, and rejections.
"""

import logging
from application.events import EventBus, EventPriority
from application.events.types import (
    RaceSubmittedEvent,
    RaceApprovedEvent,
    RaceRejectedEvent,
)

logger = logging.getLogger(__name__)


@EventBus.on(RaceSubmittedEvent, priority=EventPriority.HIGH)
async def log_race_submitted(event: RaceSubmittedEvent) -> None:
    """Log race submission to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the racer who submitted
    user = (
        await user_repo.get_by_id(event.racer_user_id) if event.racer_user_id else None
    )

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
        event.racer_user_id,
    )


@EventBus.on(RaceApprovedEvent, priority=EventPriority.HIGH)
async def log_race_approved(event: RaceApprovedEvent) -> None:
    """Log race approval to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the reviewer who approved
    user = (
        await user_repo.get_by_id(event.reviewer_user_id)
        if event.reviewer_user_id
        else None
    )

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
        event.reviewer_user_id,
    )


@EventBus.on(RaceRejectedEvent, priority=EventPriority.HIGH)
async def log_race_rejected(event: RaceRejectedEvent) -> None:
    """Log race rejection to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the reviewer who rejected
    user = (
        await user_repo.get_by_id(event.reviewer_user_id)
        if event.reviewer_user_id
        else None
    )

    await audit_service.log_action(
        user=user,
        action="race_rejected",
        details={
            "entity_id": event.entity_id,
            "tournament_id": event.tournament_id,
            "racer_user_id": event.racer_user_id,
            "reason": event.reason,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged race rejection: race_id=%s, reviewer_id=%s",
        event.entity_id,
        event.reviewer_user_id,
    )


logger.debug("Race event listeners registered")
