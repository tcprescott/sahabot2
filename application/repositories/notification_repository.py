"""
Notification repository.

Data access layer for notification subscriptions and logs.
"""

import logging
from typing import Optional
from tortoise.queryset import Q
from models import (
    NotificationSubscription,
    NotificationLog,
    NotificationMethod,
    NotificationEventType,
    NotificationDeliveryStatus,
    User,
    Organization,
)

logger = logging.getLogger(__name__)


class NotificationRepository:
    """Repository for notification data access."""

    # =====================================================================
    # Subscription Management
    # =====================================================================

    async def create_subscription(
        self,
        user: User,
        event_type: NotificationEventType,
        notification_method: NotificationMethod,
        organization: Optional[Organization] = None,
    ) -> NotificationSubscription:
        """
        Create a new notification subscription.

        Args:
            user: User creating the subscription
            event_type: Type of event to subscribe to
            notification_method: How to deliver notifications
            organization: Optional organization scope

        Returns:
            Created subscription
        """
        subscription = await NotificationSubscription.create(
            user=user,
            event_type=event_type,
            notification_method=notification_method,
            organization=organization,
            is_active=True,
        )
        logger.info(
            "Created notification subscription: user=%s, event=%s, method=%s, org=%s",
            user.id,
            NotificationEventType(event_type).name,
            NotificationMethod(notification_method).name,
            organization.id if organization else None,
        )
        return subscription

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[NotificationSubscription]:
        """Get subscription by ID."""
        return await NotificationSubscription.filter(id=subscription_id).first()

    async def get_user_subscriptions(
        self,
        user_id: int,
        is_active: Optional[bool] = None,
        organization_id: Optional[int] = None,
    ) -> list[NotificationSubscription]:
        """
        Get all subscriptions for a user.

        Args:
            user_id: User ID
            is_active: Filter by active status (None = all)
            organization_id: Filter by organization (None = all)

        Returns:
            List of subscriptions
        """
        query = NotificationSubscription.filter(user_id=user_id)
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        if organization_id is not None:
            query = query.filter(organization_id=organization_id)
        
        return await query.all()

    async def get_subscriptions_for_event(
        self,
        event_type: NotificationEventType,
        organization_id: Optional[int] = None,
    ) -> list[NotificationSubscription]:
        """
        Get all active subscriptions for a specific event type.

        Args:
            event_type: Event type to find subscriptions for
            organization_id: Optional organization filter

        Returns:
            List of active subscriptions for this event
        """
        query = NotificationSubscription.filter(
            event_type=event_type,
            is_active=True,
        ).prefetch_related("user")
        
        if organization_id is not None:
            # Get subscriptions for this org OR subscriptions with no org specified
            query = query.filter(
                Q(organization_id=organization_id) | Q(organization_id__isnull=True)
            )
        
        return await query.all()

    async def update_subscription(
        self,
        subscription_id: int,
        **updates,
    ) -> Optional[NotificationSubscription]:
        """
        Update a subscription.

        Args:
            subscription_id: Subscription ID
            **updates: Fields to update

        Returns:
            Updated subscription or None if not found
        """
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            return None

        await subscription.update_from_dict(updates).save()
        logger.info("Updated notification subscription %s: %s", subscription_id, list(updates.keys()))
        return subscription

    async def delete_subscription(self, subscription_id: int) -> bool:
        """
        Delete a subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            True if deleted, False if not found
        """
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            return False

        await subscription.delete()
        logger.info("Deleted notification subscription %s", subscription_id)
        return True

    # =====================================================================
    # Notification Logging
    # =====================================================================

    async def create_notification_log(
        self,
        user: User,
        event_type: NotificationEventType,
        notification_method: NotificationMethod,
        event_data: dict,
        delivery_status: NotificationDeliveryStatus = NotificationDeliveryStatus.PENDING,
    ) -> NotificationLog:
        """
        Create a notification log entry.

        Args:
            user: User to notify
            event_type: Event type
            notification_method: Delivery method
            event_data: Event details
            delivery_status: Initial status

        Returns:
            Created log entry
        """
        log = await NotificationLog.create(
            user=user,
            event_type=event_type,
            notification_method=notification_method,
            event_data=event_data,
            delivery_status=delivery_status,
        )
        logger.debug("Created notification log %s for user %s", log.id, user.id)
        return log

    async def update_notification_log(
        self,
        log_id: int,
        **updates,
    ) -> Optional[NotificationLog]:
        """
        Update a notification log.

        Args:
            log_id: Log ID
            **updates: Fields to update

        Returns:
            Updated log or None if not found
        """
        log = await NotificationLog.filter(id=log_id).first()
        if not log:
            return None

        await log.update_from_dict(updates).save()
        return log

    async def get_user_notification_history(
        self,
        user_id: int,
        limit: int = 50,
    ) -> list[NotificationLog]:
        """
        Get notification history for a user.

        Args:
            user_id: User ID
            limit: Maximum number of logs to return

        Returns:
            List of notification logs (most recent first)
        """
        return await NotificationLog.filter(user_id=user_id).limit(limit).all()
