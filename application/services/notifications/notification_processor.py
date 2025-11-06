"""
Background notification processor.

Polls for pending notifications and dispatches them to appropriate handlers.
Runs as a background task in the application lifecycle.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

from models import User
from models.notification_log import NotificationLog, NotificationDeliveryStatus
from models.notification_subscription import NotificationMethod, NotificationEventType
from application.services.notifications.handlers.discord_handler import DiscordNotificationHandler

logger = logging.getLogger(__name__)


class NotificationProcessor:
    """
    Background processor for pending notifications.

    Polls the notification_logs table for PENDING/RETRYING notifications
    and dispatches them to the appropriate handler based on notification_method.
    """

    def __init__(self, poll_interval: int = 30, max_retries: int = 3):
        """
        Initialize the notification processor.

        Args:
            poll_interval: Seconds between polling cycles (default: 30)
            max_retries: Maximum retry attempts for failed notifications (default: 3)
        """
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.discord_handler = DiscordNotificationHandler()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background processor."""
        if self._running:
            logger.warning("Notification processor already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Notification processor started (poll interval: %ds)", self.poll_interval)

    async def stop(self):
        """Stop the background processor."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Notification processor stopped")

    async def _process_loop(self):
        """Main processing loop."""
        while self._running:
            try:
                await self._process_pending_notifications()
            except Exception as e:
                logger.exception("Error in notification processor loop: %s", str(e))

            # Wait before next poll
            try:
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    async def _process_pending_notifications(self):
        """Process all pending notifications."""
        # Get pending/retrying notifications
        pending = await NotificationLog.filter(
            delivery_status__in=[
                NotificationDeliveryStatus.PENDING,
                NotificationDeliveryStatus.RETRYING
            ]
        ).prefetch_related('user').order_by('created_at').limit(100)

        if not pending:
            return

        logger.info("Processing %d pending notification(s)", len(pending))

        for notification in pending:
            # Check retry limit
            if notification.retry_count >= self.max_retries:
                logger.warning(
                    "Notification %d exceeded max retries (%d), marking as failed",
                    notification.id,
                    self.max_retries
                )
                notification.delivery_status = NotificationDeliveryStatus.FAILED
                notification.error_message = f"Exceeded max retries ({self.max_retries})"
                notification.sent_at = datetime.now(timezone.utc)
                await notification.save()
                continue

            # Dispatch to handler
            try:
                await self._dispatch_notification(notification)
            except Exception as e:
                logger.exception(
                    "Error dispatching notification %d: %s",
                    notification.id,
                    str(e)
                )
                notification.delivery_status = NotificationDeliveryStatus.FAILED
                notification.error_message = f"Dispatch error: {str(e)}"
                notification.sent_at = datetime.now(timezone.utc)
                notification.retry_count += 1
                await notification.save()

    async def _dispatch_notification(self, notification: NotificationLog):
        """
        Dispatch a single notification to the appropriate handler.

        Args:
            notification: NotificationLog to dispatch
        """
        user = notification.user
        if not user:
            logger.error("Notification %d has no user", notification.id)
            notification.delivery_status = NotificationDeliveryStatus.FAILED
            notification.error_message = "No user associated with notification"
            notification.sent_at = datetime.now(timezone.utc)
            await notification.save()
            return

        # Route to handler based on notification method
        if notification.notification_method == NotificationMethod.DISCORD_DM:
            await self._handle_discord_notification(notification, user)
        elif notification.notification_method == NotificationMethod.EMAIL:
            # TODO: Implement email handler
            logger.warning("Email notifications not yet implemented")
            notification.delivery_status = NotificationDeliveryStatus.FAILED
            notification.error_message = "Email handler not implemented"
            notification.sent_at = datetime.now(timezone.utc)
            await notification.save()
        elif notification.notification_method == NotificationMethod.WEBHOOK:
            # TODO: Implement webhook handler
            logger.warning("Webhook notifications not yet implemented")
            notification.delivery_status = NotificationDeliveryStatus.FAILED
            notification.error_message = "Webhook handler not implemented"
            notification.sent_at = datetime.now(timezone.utc)
            await notification.save()
        else:
            logger.error(
                "Unknown notification method: %s",
                notification.notification_method
            )
            notification.delivery_status = NotificationDeliveryStatus.FAILED
            notification.error_message = f"Unknown notification method: {notification.notification_method}"
            notification.sent_at = datetime.now(timezone.utc)
            await notification.save()

    async def _handle_discord_notification(
        self,
        notification: NotificationLog,
        user: User
    ):
        """
        Handle a Discord DM notification.

        Args:
            notification: NotificationLog to send
            user: User to send to
        """
        event_type = NotificationEventType(notification.event_type)
        event_data = notification.event_data or {}

        # Use the handler's send_notification method which routes to specific handlers
        status, error = await self.discord_handler.send_notification(
            user, event_type, event_data
        )

        # Update notification status
        notification.delivery_status = status
        notification.error_message = error
        notification.sent_at = datetime.now(timezone.utc)
        
        if status == NotificationDeliveryStatus.RETRYING:
            notification.retry_count += 1
        
        await notification.save()

        logger.info(
            "Dispatched Discord notification %d to user %s: %s",
            notification.id,
            user.discord_username,
            status.name
        )


# Global processor instance
_processor: Optional[NotificationProcessor] = None


def get_notification_processor() -> NotificationProcessor:
    """Get the global notification processor instance."""
    global _processor
    if _processor is None:
        _processor = NotificationProcessor()
    return _processor


async def start_notification_processor():
    """Start the notification processor (called from app lifespan)."""
    processor = get_notification_processor()
    await processor.start()


async def stop_notification_processor():
    """Stop the notification processor (called from app lifespan)."""
    processor = get_notification_processor()
    await processor.stop()
