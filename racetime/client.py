"""
Racetime.gg bot client implementation.

This module provides a bot client for racetime.gg integration.
"""

import asyncio
import logging
from typing import Optional
from racetime_bot import Bot, RaceHandler, monitor_cmd
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class SahaRaceHandler(RaceHandler):
    """
    Race handler for SahaBot2.
    
    Handles individual race rooms and commands.
    """
    
    @monitor_cmd
    async def ex_test(self, args, message):
        """
        Test command for the racetime bot.
        
        Usage: !test
        """
        await self.send_message("Racetime bot test command received!")
    
    async def begin(self):
        """
        Called when the handler is first created.
        
        Use this to perform initial setup for the race.
        """
        logger.info("Race handler started for race: %s", self.data.get('name'))
        # TODO: Implement initial setup logic
    
    async def end(self):
        """
        Called when the handler is being torn down.
        
        Use this to perform cleanup.
        """
        logger.info("Race handler ended for race: %s", self.data.get('name'))
        # TODO: Implement cleanup logic
    
    async def race_data(self, data):
        """
        Called whenever race data is updated.
        
        Args:
            data: Updated race data from racetime.gg
        """
        # TODO: Implement race data update logic
        pass


class RacetimeBot(Bot):
    """
    Custom racetime.gg bot client for SahaBot2.
    
    This bot integrates with racetime.gg to provide race management
    and monitoring functionality.
    """
    
    def __init__(self, category_slug: str, client_id: str, client_secret: str):
        """
        Initialize the racetime bot with configuration.
        
        Args:
            category_slug: The racetime.gg category (e.g., 'alttpr')
            client_id: OAuth2 client ID for this category
            client_secret: OAuth2 client secret for this category
        """
        super().__init__(
            category_slug=category_slug,
            client_id=client_id,
            client_secret=client_secret,
            logger=logger,
        )
        self.category_slug = category_slug
        logger.info("Racetime bot initialized for category: %s", category_slug)
    
    async def should_handle(self, race_data: dict) -> bool:
        """
        Determine if this bot should handle a specific race.
        
        Args:
            race_data: Race data from racetime.gg
            
        Returns:
            bool: True if bot should handle this race
        """
        # TODO: Implement race filtering logic
        # For now, handle all races in the configured category
        return True
    
    async def make_handler(self, race_data: dict) -> SahaRaceHandler:
        """
        Create a race handler for a specific race.
        
        Args:
            race_data: Race data from racetime.gg
            
        Returns:
            SahaRaceHandler instance for this race
        """
        return SahaRaceHandler(race_data, self, state=self.state)


# Map of category -> bot instance
_racetime_bots: dict[str, RacetimeBot] = {}
_racetime_bot_tasks: dict[str, asyncio.Task] = {}


async def start_racetime_bot(
    category: str,
    client_id: str,
    client_secret: str
) -> RacetimeBot:
    """
    Start a racetime bot for a specific category.
    
    Args:
        category: The racetime.gg category slug (e.g., 'alttpr')
        client_id: OAuth2 client ID for this category
        client_secret: OAuth2 client secret for this category
    
    Returns:
        RacetimeBot instance for the category
        
    Raises:
        RuntimeError: If bot for this category is already running
    """
    global _racetime_bots, _racetime_bot_tasks
    
    if category in _racetime_bots:
        raise RuntimeError("Racetime bot for category %s is already running" % category)
    
    logger.info("Starting racetime bot for category: %s", category)
    
    # Create bot instance with category-specific credentials
    bot = RacetimeBot(
        category_slug=category,
        client_id=client_id,
        client_secret=client_secret,
    )
    
    # Store the bot instance
    _racetime_bots[category] = bot
    
    # Start the bot in a background task
    _racetime_bot_tasks[category] = asyncio.create_task(bot.run())
    
    logger.info("Racetime bot started successfully for category: %s", category)
    return bot


async def stop_racetime_bot(category: str) -> None:
    """
    Stop the racetime bot for a specific category.
    
    Args:
        category: The racetime.gg category slug
    """
    global _racetime_bots, _racetime_bot_tasks
    
    if category not in _racetime_bots:
        logger.warning("Racetime bot for category %s is not running", category)
        return
    
    logger.info("Stopping racetime bot for category: %s", category)
    
    try:
        # Stop the bot task
        task = _racetime_bot_tasks.get(category)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        logger.info("Racetime bot stopped successfully for category: %s", category)
    
    except Exception as e:
        logger.error("Error stopping racetime bot for category %s: %s", category, e, exc_info=True)
    
    finally:
        _racetime_bots.pop(category, None)
        _racetime_bot_tasks.pop(category, None)


async def stop_all_racetime_bots() -> None:
    """
    Stop all running racetime bots.
    
    Stops all bot instances gracefully and cleans up resources.
    """
    categories = list(_racetime_bots.keys())
    
    if not categories:
        logger.info("No racetime bots running")
        return
    
    logger.info("Stopping all racetime bots (%d instances)", len(categories))
    
    for category in categories:
        await stop_racetime_bot(category)


def get_racetime_bot_instance(category: str) -> Optional[RacetimeBot]:
    """
    Get the racetime bot instance for a specific category.
    
    Args:
        category: The racetime.gg category slug
    
    Returns:
        RacetimeBot instance or None if not running
    """
    return _racetime_bots.get(category)


def get_all_racetime_bot_instances() -> dict[str, RacetimeBot]:
    """
    Get all running racetime bot instances.
    
    Returns:
        Dictionary mapping category -> RacetimeBot instance
    """
    return _racetime_bots.copy()
