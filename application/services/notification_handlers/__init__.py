"""
Notification handlers package.

Contains handlers for different notification delivery methods (Discord, Email, etc).
"""

from .base_handler import BaseNotificationHandler
from .discord_handler import DiscordNotificationHandler

__all__ = ['BaseNotificationHandler', 'DiscordNotificationHandler']
