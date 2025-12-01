"""
Notifications Plugin services.

This module re-exports notification services from the core application
to provide a unified interface through the plugin system.
"""

from application.services.notifications.notification_service import NotificationService
from application.services.notifications.notification_processor import (
    NotificationProcessor,
)

__all__ = [
    "NotificationService",
    "NotificationProcessor",
]
