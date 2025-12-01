"""
DiscordEvents Plugin models.

This module re-exports Discord Scheduled Event models from the core application
to provide a unified interface through the plugin system.
"""

from models.discord_scheduled_event import DiscordScheduledEvent

__all__ = [
    "DiscordScheduledEvent",
]
