"""
Notifications Plugin event types.

This module defines event types for notification operations.
"""

from dataclasses import dataclass
from typing import Optional

from application.events.base import BaseEvent


@dataclass(frozen=True)
class NotificationSentEvent(BaseEvent):
    """Emitted when a notification is successfully sent."""

    notification_log_id: int = 0
    event_type_code: int = 0  # NotificationEventType value
    method: int = 0  # NotificationMethod value

    @property
    def event_type(self) -> str:
        return "notification.sent"


@dataclass(frozen=True)
class NotificationFailedEvent(BaseEvent):
    """Emitted when a notification fails to send."""

    notification_log_id: int = 0
    event_type_code: int = 0  # NotificationEventType value
    method: int = 0  # NotificationMethod value
    error_message: Optional[str] = None
    retry_count: int = 0

    @property
    def event_type(self) -> str:
        return "notification.failed"


@dataclass(frozen=True)
class SubscriptionCreatedEvent(BaseEvent):
    """Emitted when a notification subscription is created."""

    subscription_id: int = 0
    event_type_code: int = 0  # NotificationEventType value
    method: int = 0  # NotificationMethod value

    @property
    def event_type(self) -> str:
        return "notification.subscription.created"


@dataclass(frozen=True)
class SubscriptionUpdatedEvent(BaseEvent):
    """Emitted when a notification subscription is updated."""

    subscription_id: int = 0
    is_active: bool = True

    @property
    def event_type(self) -> str:
        return "notification.subscription.updated"
