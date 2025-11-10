"""
Base notification handler.

Provides abstract base class for all notification delivery methods.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from models import User
from models.notification_log import NotificationDeliveryStatus
from models.notification_subscription import NotificationEventType

logger = logging.getLogger(__name__)


class BaseNotificationHandler(ABC):
    """
    Abstract base class for notification handlers.

    Defines the interface that all notification delivery methods must implement.
    Subclasses should implement the delivery mechanism (Discord, email, webhook, etc.)
    and the event-specific formatting methods.
    """

    @abstractmethod
    async def send_notification(
        self, user: User, event_type: NotificationEventType, event_data: dict
    ) -> tuple[NotificationDeliveryStatus, Optional[str]]:
        """
        Send a notification to a user.

        This is the main entry point for sending notifications.
        Subclasses should implement the specific delivery mechanism.

        Args:
            user: User to send notification to
            event_type: Type of notification event
            event_data: Event-specific data for formatting the notification

        Returns:
            Tuple of (delivery_status, error_message)
            - delivery_status: SENT if successful, FAILED if failed
            - error_message: Error description if failed, None if successful
        """
        raise NotImplementedError("Subclasses must implement send_notification()")

    # Event-specific formatting methods
    # Subclasses can override these to provide custom formatting

    async def format_match_scheduled(self, event_data: dict) -> dict:
        """Format match scheduled notification data."""
        return event_data

    async def format_match_completed(self, event_data: dict) -> dict:
        """Format match completed notification data."""
        return event_data

    async def format_tournament_created(self, event_data: dict) -> dict:
        """Format tournament created notification data."""
        return event_data

    async def format_tournament_started(self, event_data: dict) -> dict:
        """Format tournament started notification data."""
        return event_data

    async def format_tournament_ended(self, event_data: dict) -> dict:
        """Format tournament ended notification data."""
        return event_data

    async def format_tournament_updated(self, event_data: dict) -> dict:
        """Format tournament updated notification data."""
        return event_data

    async def format_race_submitted(self, event_data: dict) -> dict:
        """Format race submitted notification data."""
        return event_data

    async def format_race_approved(self, event_data: dict) -> dict:
        """Format race approved notification data."""
        return event_data

    async def format_race_rejected(self, event_data: dict) -> dict:
        """Format race rejected notification data."""
        return event_data

    async def format_crew_approved(self, event_data: dict) -> dict:
        """Format crew approved notification data."""
        return event_data

    async def format_crew_removed(self, event_data: dict) -> dict:
        """Format crew removed notification data."""
        return event_data

    async def format_invite_received(self, event_data: dict) -> dict:
        """Format invite received notification data."""
        return event_data

    async def format_organization_member_added(self, event_data: dict) -> dict:
        """Format organization member added notification data."""
        return event_data

    async def format_organization_member_removed(self, event_data: dict) -> dict:
        """Format organization member removed notification data."""
        return event_data

    async def format_organization_permission_changed(self, event_data: dict) -> dict:
        """Format organization permission changed notification data."""
        return event_data

    async def format_user_permission_changed(self, event_data: dict) -> dict:
        """Format user permission changed notification data."""
        return event_data
