"""
Notifications Plugin models.

This module re-exports notification models from the core application
to provide a unified interface through the plugin system.
"""

from models.notification_subscription import (
    NotificationSubscription,
    NotificationMethod,
    NotificationEventType,
)
from models.notification_log import (
    NotificationLog,
    NotificationDeliveryStatus,
)

__all__ = [
    "NotificationSubscription",
    "NotificationMethod",
    "NotificationEventType",
    "NotificationLog",
    "NotificationDeliveryStatus",
]
