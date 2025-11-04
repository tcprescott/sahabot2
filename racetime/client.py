"""
Racetime.gg bot client implementation.

This module provides a bot client for racetime.gg integration.
"""

import asyncio
import logging
from typing import Optional
from racetime_bot import Bot, RaceHandler, monitor_cmd
from models import BotStatus
from application.repositories.racetime_bot_repository import RacetimeBotRepository
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class SahaRaceHandler(RaceHandler):
    """
    Race handler for SahaBot2.
    
    Handles individual race rooms and commands.
    """
    
    @monitor_cmd
    async def ex_test(self, _args, _message):
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
    # Initial setup hook for race handler
    
    async def end(self):
        """
        Called when the handler is being torn down.
        
        Use this to perform cleanup.
        """
        logger.info("Race handler ended for race: %s", self.data.get('name'))
    # Cleanup hook for race handler
    
    async def race_data(self, data):
        """
        Called whenever race data is updated.
        
        Args:
            data: Updated race data from racetime.gg
        """
    # Handle race data updates (placeholder)
    logger.debug("Race data update received")


class RacetimeBot(Bot):
    """
    Custom racetime.gg bot client for SahaBot2.
    
    This bot integrates with racetime.gg to provide race management
    and monitoring functionality.
    """
    
    # Override the default racetime host and security settings with configured values
    # Extract just the hostname from the full URL (e.g., "http://localhost:8000" -> "localhost:8000")
    racetime_host = settings.RACETIME_URL.replace('https://', '').replace('http://', '').rstrip('/')
    # Determine if TLS/SSL should be used based on URL scheme
    racetime_secure = settings.RACETIME_URL.startswith('https://')
    
    def __init__(self, category_slug: str, client_id: str, client_secret: str, bot_id: Optional[int] = None):
        """
        Initialize the racetime bot with configuration.
        
        Args:
            category_slug: The racetime.gg category (e.g., 'alttpr')
            client_id: OAuth2 client ID for this category
            client_secret: OAuth2 client secret for this category
            bot_id: Optional database ID for status tracking
        """
        logger.info(
            "Initializing racetime bot with category=%s, client_id=%s, client_secret=%s... (host: %s, secure: %s)",
            category_slug,
            client_id,
            client_secret[:10] + "..." if len(client_secret) > 10 else "***",
            self.racetime_host,
            self.racetime_secure
        )
        try:
            super().__init__(
                category_slug=category_slug,
                client_id=client_id,
                client_secret=client_secret,
                logger=logger,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize racetime bot for category %s: %s. "
                "Please verify that an OAuth2 application exists in your racetime instance "
                "with these credentials and uses the 'client_credentials' grant type.",
                category_slug,
                e
            )
            raise
        self.category_slug = category_slug
        self.bot_id = bot_id
        logger.info(
            "Racetime bot initialized successfully for category: %s",
            category_slug
        )
    
    def should_handle(self, race_data: dict) -> bool:
        """
        Determine if this bot should handle a specific race.
        
        Args:
            race_data: Race data from racetime.gg
            
        Returns:
            bool: True if bot should handle this race
        """
    # Handle all races in the configured category
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
    client_secret: str,
    bot_id: Optional[int] = None,
    max_retries: int = 5,
    initial_backoff: float = 5.0,
) -> RacetimeBot:
    """
    Start a racetime bot for a specific category with retry logic.
    
    The bot will automatically retry on connection failures with exponential backoff.
    Authentication failures will not be retried.
    
    Args:
        category: The racetime.gg category slug
        client_id: OAuth2 client ID for this category
        client_secret: OAuth2 client secret for this category
        bot_id: Optional database ID for status tracking
        max_retries: Maximum number of retry attempts (default: 5)
        initial_backoff: Initial backoff delay in seconds (default: 5.0)
        
    Returns:
        RacetimeBot instance (bot runs in background task)
        
    Raises:
        Exception: If bot initialization or starting fails
    """
    logger.info(
        "Starting racetime bot for category: %s (bot_id=%s)",
        category,
        bot_id
    )
    
    try:
        # Create bot instance with category-specific credentials
        bot = RacetimeBot(
            category_slug=category,
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
        )
        
        # Store the bot instance
        _racetime_bots[category] = bot
        
        # Start the bot in a background task with error handling and retry logic
        async def run_with_status_tracking():
            """Run bot and track connection status with automatic retry on failure."""
            repository = RacetimeBotRepository()
            retry_count = 0
            backoff_delay = initial_backoff
            
            while True:
                try:
                    logger.info("Starting bot.run() for category: %s (attempt %d/%d)", 
                               category, retry_count + 1, max_retries + 1)
                    logger.debug("Bot configuration - host: %s, secure: %s", 
                                bot.racetime_host, bot.racetime_secure)
                    
                    # Update status to connected when starting
                    if bot_id:
                        await repository.record_connection_success(bot_id)
                    
                    # Reset retry count on successful connection
                    retry_count = 0
                    backoff_delay = initial_backoff
                    
                    # Instead of calling bot.run() which tries to take over the event loop,
                    # we manually create the tasks that run() would create
                    # This allows the bot to work within our existing async context
                    reauth_task = asyncio.create_task(bot.reauthorize())
                    refresh_task = asyncio.create_task(bot.refresh_races())
                    
                    # Wait for both tasks (they run forever until cancelled)
                    await asyncio.gather(reauth_task, refresh_task)
                    
                    logger.info("bot tasks completed normally for category: %s", category)
                    break  # Exit retry loop on normal completion
                    
                except asyncio.CancelledError:
                    # Bot was cancelled (stopped manually) - don't retry
                    logger.info("Racetime bot %s was cancelled (CancelledError caught)", category)
                    if bot_id:
                        await repository.update_bot_status(
                            bot_id, BotStatus.DISCONNECTED, status_message="Bot stopped"
                        )
                    raise  # Re-raise to properly handle cancellation
                    
                except Exception as e:
                    # Always log the full exception with traceback
                    logger.error(
                        "Racetime bot error for %s (attempt %d/%d): %s",
                        category,
                        retry_count + 1,
                        max_retries + 1,
                        e,
                        exc_info=True
                    )
                    
                    # Check if this is an auth error (don't retry auth failures)
                    error_msg = str(e)
                    is_auth_error = "auth" in error_msg.lower() or "unauthorized" in error_msg.lower() or "401" in error_msg
                    
                    # Update status based on error type
                    if bot_id:
                        if is_auth_error:
                            await repository.record_connection_failure(
                                bot_id, error_msg, BotStatus.AUTH_FAILED
                            )
                        else:
                            await repository.record_connection_failure(
                                bot_id, error_msg, BotStatus.CONNECTION_ERROR
                            )
                    
                    # Don't retry on auth errors
                    if is_auth_error:
                        logger.error("Authentication failed for bot %s - not retrying", category)
                        break
                    
                    # Check if we should retry
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(
                            "Max retries (%d) reached for bot %s - giving up",
                            max_retries,
                            category
                        )
                        break
                    
                    # Wait with exponential backoff before retrying
                    logger.info(
                        "Retrying bot %s in %.1f seconds (attempt %d/%d)...",
                        category,
                        backoff_delay,
                        retry_count + 1,
                        max_retries + 1
                    )
                    await asyncio.sleep(backoff_delay)
                    
                    # Exponential backoff (double the delay each time, max 5 minutes)
                    backoff_delay = min(backoff_delay * 2, 300.0)
            
            # Cleanup happens in finally block below
            
        async def run_wrapper():
            """Wrapper to ensure cleanup happens."""
            try:
                await run_with_status_tracking()
            finally:
                # Clean up bot instance when task completes (for any reason)
                logger.info("Cleaning up racetime bot for category: %s", category)
                logger.debug("Removing from _racetime_bots: %s", category)
                _racetime_bots.pop(category, None)
                logger.debug("Removing from _racetime_bot_tasks: %s", category)
                _racetime_bot_tasks.pop(category, None)
                logger.info("Racetime bot task completed and cleaned up for category: %s", category)
        
        _racetime_bot_tasks[category] = asyncio.create_task(run_wrapper())
        
        logger.info("Racetime bot started successfully for category: %s", category)
        return bot
        
    except Exception as e:
        logger.error("Failed to start racetime bot for %s: %s", category, e, exc_info=True)
        
        # Update status to connection error
        if bot_id:
            repository = RacetimeBotRepository()
            error_msg = str(e)
            if "auth" in error_msg.lower() or "unauthorized" in error_msg.lower():
                await repository.record_connection_failure(
                    bot_id, error_msg, BotStatus.AUTH_FAILED
                )
            else:
                await repository.record_connection_failure(
                    bot_id, error_msg, BotStatus.CONNECTION_ERROR
                )
        raise


async def stop_racetime_bot(category: str) -> None:
    """
    Stop the racetime bot for a specific category.
    
    Args:
        category: The racetime.gg category slug
    """
    logger.info("Attempting to stop racetime bot for category: %s", category)
    logger.debug("Current bots: %s", list(_racetime_bots.keys()))
    logger.debug("Current tasks: %s", list(_racetime_bot_tasks.keys()))
    
    # Check for the task (not the bot instance, which may already be cleaned up)
    task = _racetime_bot_tasks.get(category)
    if not task:
        logger.warning("No task found for racetime bot category %s", category)
        return
    
    if task.done():
        logger.info("Racetime bot task for category %s is already done", category)
        return
    
    logger.info("Cancelling racetime bot task for category: %s", category)
    
    try:
        # Cancel the bot task (cleanup happens in the task's finally block)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            # Expected when cancelling
            logger.info("Racetime bot task cancelled successfully for category: %s", category)
        
        logger.info("Racetime bot stopped successfully for category: %s", category)
    
    except Exception as e:
        logger.error("Error stopping racetime bot for category %s: %s", category, e, exc_info=True)


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
