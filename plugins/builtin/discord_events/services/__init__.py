"""
DiscordEvents Plugin services.

This module re-exports Discord Scheduled Event services from the core application
to provide a unified interface through the plugin system.
"""

from application.services.discord.discord_scheduled_event_service import (
    DiscordScheduledEventService,
)

__all__ = [
    "DiscordScheduledEventService",
]
