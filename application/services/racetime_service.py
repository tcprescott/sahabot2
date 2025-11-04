"""
Racetime Service for SahaBot2

Encapsulates starting and stopping racetime.gg bot instances as part of the
application services layer. The main application should call into this service
rather than using the client module directly.

Note: Bot configurations are now loaded from the database (RacetimeBot model)
rather than from environment settings.
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional, Tuple

from models import RacetimeBot
from racetime.client import start_racetime_bot, stop_all_racetime_bots

logger = logging.getLogger(__name__)

ConfigTuple = Tuple[str, str, str]


class RacetimeService:
    """Service facade for managing Racetime bot lifecycle."""

    @staticmethod
    async def start_all(configs: Optional[Iterable[ConfigTuple]] = None) -> int:
        """
        Start racetime bots for all configured categories.

        If no configs are provided, loads active bots from the database.

        Args:
            configs: Optional iterable of (category, client_id, client_secret).
                     If not provided, loads from database.

        Returns:
            int: Number of bots started successfully.
        """
        started = 0

        # Load configs from database if not provided
        if configs is None:
            bots = await RacetimeBot.filter(is_active=True).all()
            # Build configs with bot_id included
            cfgs = [(bot.category, bot.client_id, bot.client_secret, bot.id) for bot in bots]
        else:
            # Legacy mode: configs without bot_id
            cfgs = [(cat, cid, csec, None) for cat, cid, csec in configs]

        if not cfgs:
            logger.info("No racetime bots configured")
            return 0

        logger.info("Starting %d racetime bot(s)", len(cfgs))

        for category, client_id, client_secret, bot_id in cfgs:
            try:
                await start_racetime_bot(category, client_id, client_secret, bot_id=bot_id)
                logger.info("Racetime bot started for category: %s (bot_id=%s)", category, bot_id)
                started += 1
            except Exception as e:
                logger.error(
                    "Failed to start Racetime bot for category %s: %s",
                    category,
                    e,
                    exc_info=True,
                )
                logger.warning(
                    "Application will continue without Racetime bot for %s",
                    category,
                )
        return started

    @staticmethod
    async def stop_all() -> None:
        """Stop all running racetime bots (best-effort)."""
        try:
            await stop_all_racetime_bots()
        except Exception as e:
            logger.error("Error stopping Racetime bots: %s", e, exc_info=True)
