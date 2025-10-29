"""
Discord bot package for SahaBot2.

This package contains the Discord bot implementation that runs
as a singleton service within the NiceGUI application.
"""

from bot.client import DiscordBot, get_bot_instance

__all__ = [
    'DiscordBot',
    'get_bot_instance',
]
