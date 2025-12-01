"""
DiscordEvents Plugin for SahaBot2.

Provides Discord Scheduled Events integration including:
- Auto-creation of Discord events for tournament matches
- Event status synchronization
- Orphaned event cleanup
"""

from plugins.builtin.discord_events.plugin import DiscordEventsPlugin

__all__ = ["DiscordEventsPlugin"]
