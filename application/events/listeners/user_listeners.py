"""
User domain event listeners.

Handles audit logging for user lifecycle events and permission changes.
"""

import logging
from application.events import EventBus, EventPriority
from application.events.types import (
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeletedEvent,
    UserPermissionChangedEvent,
)

logger = logging.getLogger(__name__)


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
        event.new_permission,
    )


@EventBus.on(UserUpdatedEvent, priority=EventPriority.HIGH)
async def log_user_updated(event: UserUpdatedEvent) -> None:
    """Log user update to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who performed the action
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="user_updated",
        details={
            "entity_id": event.entity_id,
            "changed_fields": event.changed_fields,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged user update: user_id=%s", event.entity_id)


@EventBus.on(UserDeletedEvent, priority=EventPriority.HIGH)
async def log_user_deleted(event: UserDeletedEvent) -> None:
    """Log user deletion to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who performed the action
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="user_deleted",
        details={
            "entity_id": event.entity_id,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged user deletion: user_id=%s", event.entity_id)


logger.debug("User event listeners registered")
