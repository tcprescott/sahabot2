"""
Notification service.

Business logic for managing user notification subscriptions and delivery.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
from models import (
    User,
    Organization,
    NotificationSubscription,
    NotificationMethod,
    NotificationEventType,
    NotificationDeliveryStatus,
)
from application.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and subscriptions."""

    def __init__(self):
        self.repository = NotificationRepository()

    # =====================================================================
    # Subscription Management
    # =====================================================================

    async def subscribe(
        self,
        user: User,
        event_type: NotificationEventType,
        notification_method: NotificationMethod,
        organization: Optional[Organization] = None,
    ) -> Optional[NotificationSubscription]:
        """
        Subscribe a user to event notifications.

        Authorization: User can only create subscriptions for themselves
        (enforced by passing user parameter to repository).

        Args:
            user: User creating the subscription
            event_type: Event type to subscribe to
            notification_method: How to deliver notifications
            organization: Optional organization scope

        Returns:
            Created or existing subscription
        """
        try:
            # Check if subscription already exists
            existing = await self.repository.get_user_subscriptions(
                user_id=user.id,
                is_active=True,
            )

            for sub in existing:
                if (
                    sub.event_type == event_type
                    and sub.notification_method == notification_method
                    and getattr(sub, "organization_id", None)
                    == (organization.id if organization else None)
                ):
                    logger.info("Subscription already exists for user %s", user.id)
                    return sub

            # Create new subscription
            return await self.repository.create_subscription(
                user=user,
                event_type=event_type,
                notification_method=notification_method,
                organization=organization,
            )
        except Exception as e:
            logger.error("Failed to create subscription: %s", e, exc_info=True)
            return None

    async def unsubscribe(
        self,
        user: User,
        event_type: NotificationEventType,
        notification_method: NotificationMethod,
        organization: Optional[Organization] = None,
    ) -> bool:
        """
        Unsubscribe from event notifications.

        Args:
            user: User unsubscribing
            event_type: Event type
            notification_method: Notification method
            organization: Optional organization scope

        Returns:
            True if unsubscribed, False otherwise
        """
        subscriptions = await self.repository.get_user_subscriptions(
            user_id=user.id,
            is_active=True,
        )

        for sub in subscriptions:
            if (
                sub.event_type == event_type
                and sub.notification_method == notification_method
                and getattr(sub, "organization_id", None)
                == (organization.id if organization else None)
            ):
                await self.repository.delete_subscription(sub.id)
                logger.info(
                    "User %s unsubscribed from %s",
                    user.id,
                    NotificationEventType(event_type).name,
                )
                return True

        return False

    async def get_user_subscriptions(
        self,
        user: User,
        organization: Optional[Organization] = None,
    ) -> list[NotificationSubscription]:
        """
        Get all subscriptions for a user.

        Authorization: User can only view their own subscriptions
        (enforced by user_id filter in repository query).

        Args:
            user: User
            organization: Optional organization filter

        Returns:
            List of subscriptions
        """
        return await self.repository.get_user_subscriptions(
            user_id=user.id,
            is_active=True,
            organization_id=organization.id if organization else None,
        )

    async def toggle_subscription(
        self,
        subscription_id: int,
        user: User,
    ) -> Optional[NotificationSubscription]:
        """
        Toggle a subscription's active status.

        Args:
            subscription_id: Subscription ID
            user: User (for authorization)

        Returns:
            Updated subscription or None
        """
        subscription = await self.repository.get_subscription_by_id(subscription_id)
        if not subscription:
            return None

        # Verify ownership
        if getattr(subscription, "user_id", None) != user.id:
            logger.warning(
                "User %s attempted to toggle subscription %s they don't own",
                user.id,
                subscription_id,
            )
            return None

        return await self.repository.update_subscription(
            subscription_id,
            is_active=not subscription.is_active,
        )

    # =====================================================================
    # Notification Delivery (stub for now - handlers will implement)
    # =====================================================================

    async def queue_notification(
        self,
        user: User,
        event_type: NotificationEventType,
        event_data: dict,
        organization_id: Optional[int] = None,
    ) -> list[int]:
        """
        Queue notifications for a user based on their subscriptions.

        This method creates notification log entries that will be processed
        by the appropriate handlers (Discord, Email, etc).

        Authorization: Notifications are created for the specified user only
        (user parameter scopes the operation).

        Args:
            user: User to notify
            event_type: Type of event
            event_data: Event details
            organization_id: Organization context (optional)

        Returns:
            List of created notification log IDs
        """
        # Get ALL active subscriptions for this user
        # We'll filter by event type and organization scope manually
        subscriptions = await self.repository.get_user_subscriptions(
            user_id=user.id,
            is_active=True,
        )

        # Filter to matching event types and organization scope
        matching = []
        for sub in subscriptions:
            # Must match event type
            if sub.event_type != event_type:
                continue

            # Check organization scope:
            # - If subscription has organization_id, it must match the event's organization_id
            # - If subscription is global (organization_id=None), it matches all organizations
            sub_org_id = getattr(sub, "organization_id", None)
            if sub_org_id is not None and sub_org_id != organization_id:
                continue

            matching.append(sub)

        if not matching:
            logger.debug(
                "No active subscriptions for user %s, event %s, org %s",
                user.id,
                NotificationEventType(event_type).name,
                organization_id,
            )
            return []

        # Create notification logs for each subscription
        log_ids = []
        for sub in matching:
            log = await self.repository.create_notification_log(
                user=user,
                event_type=event_type,
                notification_method=sub.notification_method,
                event_data=event_data,
                delivery_status=NotificationDeliveryStatus.PENDING,
            )
            log_ids.append(log.id)

        logger.info(
            "Queued %d notification(s) for user %s, event %s, org %s",
            len(log_ids),
            user.id,
            NotificationEventType(event_type).name,
            organization_id,
        )
        return log_ids

    async def queue_broadcast_notification(
        self,
        event_type: NotificationEventType,
        event_data: dict,
        organization_id: Optional[int] = None,
    ) -> list[int]:
        """
        Queue notifications for all users subscribed to an event type.

        This is used for broadcast events like tournament creation where
        we want to notify all subscribed users, not just a specific user.

        Args:
            event_type: Type of notification event
            event_data: Event-specific data to include
            organization_id: Organization scope (None for global)

        Returns:
            List of notification log IDs created
        """
        # Get all active subscriptions for this event type
        subscriptions = await self.repository.get_subscriptions_for_event(
            event_type=event_type,
            organization_id=organization_id,
        )

        log_ids = []
        for sub in subscriptions:
            log = await self.repository.create_notification_log(
                user=sub.user,
                event_type=event_type,
                notification_method=sub.notification_method,
                event_data=event_data,
                delivery_status=NotificationDeliveryStatus.PENDING,
            )
            log_ids.append(log.id)

        logger.info(
            "Queued %d broadcast notification(s) for event type %s",
            len(log_ids),
            event_type.name,
        )
        return log_ids

    async def mark_notification_sent(
        self,
        log_id: int,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Mark a notification as sent or failed.

        Args:
            log_id: Notification log ID
            error_message: Error message if failed (None if successful)

        Returns:
            True if updated
        """
        updates = {
            "delivery_status": (
                NotificationDeliveryStatus.FAILED
                if error_message
                else NotificationDeliveryStatus.SENT
            ),
            "sent_at": datetime.now(timezone.utc),
        }

        if error_message:
            updates["error_message"] = error_message

        result = await self.repository.update_notification_log(log_id, **updates)
        return result is not None
