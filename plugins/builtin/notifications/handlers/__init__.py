"""
Notifications Plugin handlers.

This module re-exports notification handlers from the core application
to provide a unified interface through the plugin system.
"""

from application.services.notifications.handlers.base_handler import (
    BaseNotificationHandler,
)
from application.services.notifications.handlers.discord_handler import (
    DiscordNotificationHandler,
)

__all__ = [
    "BaseNotificationHandler",
    "DiscordNotificationHandler",
]
