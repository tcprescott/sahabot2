"""
Notifications Plugin for SahaBot2.

Provides notification subscription and delivery:
- User notification preferences
- Multi-channel notification delivery (Discord, Email, etc.)
- Notification logging and retry handling
"""

from plugins.builtin.notifications.plugin import NotificationsPlugin

__all__ = ["NotificationsPlugin"]
