"""
Organization domain event listeners.

Handles audit logging for organization lifecycle, membership, and permission events.
"""

import logging
from application.events import EventBus, EventPriority
from application.events.types import (
    OrganizationCreatedEvent,
    OrganizationUpdatedEvent,
    OrganizationDeletedEvent,
    OrganizationMemberAddedEvent,
    OrganizationMemberRemovedEvent,
    OrganizationMemberPermissionChangedEvent,
)

logger = logging.getLogger(__name__)


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
    user = (
        await user_repo.get_by_id(event.added_by_user_id)
        if event.added_by_user_id
        else None
    )

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
        event.organization_id,
    )


@EventBus.on(OrganizationMemberRemovedEvent, priority=EventPriority.HIGH)
async def log_organization_member_removed(
    event: OrganizationMemberRemovedEvent,
) -> None:
    """Log member removal to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who removed the member
    user = (
        await user_repo.get_by_id(event.removed_by_user_id)
        if event.removed_by_user_id
        else None
    )

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
        event.organization_id,
    )


@EventBus.on(OrganizationUpdatedEvent, priority=EventPriority.HIGH)
async def log_organization_updated(event: OrganizationUpdatedEvent) -> None:
    """Log organization update to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who updated the organization
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="organization_updated",
        details={
            "entity_id": event.entity_id,
            "changed_fields": event.changed_fields,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged organization update: org_id=%s", event.entity_id)


@EventBus.on(OrganizationDeletedEvent, priority=EventPriority.HIGH)
async def log_organization_deleted(event: OrganizationDeletedEvent) -> None:
    """Log organization deletion to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who deleted the organization
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="organization_deleted",
        details={
            "entity_id": event.entity_id,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged organization deletion: org_id=%s", event.entity_id)


@EventBus.on(OrganizationMemberPermissionChangedEvent, priority=EventPriority.HIGH)
async def log_organization_member_permission_changed(
    event: OrganizationMemberPermissionChangedEvent,
) -> None:
    """Log member permission change to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who changed the permission
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="organization_member_permission_changed",
        details={
            "member_user_id": event.member_user_id,
            "organization_id": event.organization_id,
            "permission_name": event.permission_name,
            "granted": event.granted,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged member permission change: user_id=%s in org_id=%s",
        event.member_user_id,
        event.organization_id,
    )


logger.debug("Organization event listeners registered")
