"""
Discord Service for SahaBot2

This module encapsulates starting and stopping the Discord bot as part of the
application services layer. UI and main application should depend on this
service rather than calling the bot client directly.
"""

from __future__ import annotations

import logging
from typing import Optional

from discordbot.client import (
    start_bot as _start_bot,
    stop_bot as _stop_bot,
    get_bot_instance,
    DiscordBot,
)

logger = logging.getLogger(__name__)


class DiscordService:
    """Service facade for managing the Discord bot lifecycle."""

    @staticmethod
    async def start() -> bool:
        """
        Start the Discord bot.

        Returns:
            bool: True if the bot started successfully, False otherwise.
        """
        try:
            await _start_bot()
            logger.info("Discord bot started via service")
            return True
        except Exception as e:
            logger.error("Failed to start Discord bot: %s", e, exc_info=True)
            logger.warning("Application will continue without Discord bot")
            return False

    @staticmethod
    async def stop() -> None:
        """Stop the Discord bot (no-op if not running)."""
        try:
            await _stop_bot()
            logger.info("Discord bot stopped via service")
        except Exception as e:
            # Stopping should be best-effort; just log the error
            logger.error("Error stopping Discord bot: %s", e, exc_info=True)

    @staticmethod
    def instance() -> Optional[DiscordBot]:
        """Return the running Discord bot instance, if any."""
        return get_bot_instance()
