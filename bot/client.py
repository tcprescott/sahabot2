"""
Discord bot client for SahaBot2.

This module provides a singleton Discord bot that runs within the application.
"""

import discord
from discord.ext import commands
import asyncio
import logging
from typing import Optional
from config import settings

# Configure logging
logger = logging.getLogger(__name__)


class DiscordBot(commands.Bot):
    """
    Custom Discord bot client for SahaBot2.
    
    This bot runs as a singleton within the NiceGUI application and provides
    Discord integration for various features.
    """
    
    def __init__(self):
        """Initialize the Discord bot with required intents."""
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        # Initialize bot
        super().__init__(
            command_prefix='!',  # Default prefix, can be changed later
            intents=intents,
            help_command=None  # We'll implement custom help if needed
        )
        
        self._ready = False
    
    async def setup_hook(self) -> None:
        """
        Setup hook called when the bot is starting up.
        
        This is where we'll load cogs/extensions.
        """
        logger.info("Bot setup hook called")
        
        # Load command cogs
        try:
            await self.load_extension('bot.commands.test_commands')
            logger.info("Loaded test commands")
        except Exception as e:
            logger.error("Failed to load test commands: %s", e, exc_info=True)
        
        # Sync commands to Discord
        try:
            synced = await self.tree.sync()
            logger.info("Synced %d command(s) to Discord", len(synced))
        except Exception as e:
            logger.error("Failed to sync commands: %s", e, exc_info=True)
    
    async def on_ready(self) -> None:
        """Event handler called when the bot is ready."""
        self._ready = True
        logger.info('Bot is ready! Logged in as %s (ID: %s)', self.user, self.user.id)
        logger.info('Connected to %d guilds', len(self.guilds))
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for commands"
            )
        )
    
    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """
        Event handler for bot errors.
        
        Args:
            event_method: The event method that raised the error
        """
        logger.error('Error in %s', event_method, exc_info=True)
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """
        Event handler for command errors.
        
        Args:
            ctx: Command context
            error: The error that occurred
        """
        logger.error('Command error in %s: %s', ctx.command, error, exc_info=error)
    
    @property
    def is_ready(self) -> bool:
        """
        Check if the bot is ready.
        
        Returns:
            bool: True if bot is connected and ready
        """
        return self._ready and not self.is_closed()


# Singleton instance
_bot_instance: Optional[DiscordBot] = None
_bot_task: Optional[asyncio.Task] = None


def get_bot_instance() -> Optional[DiscordBot]:
    """
    Get the singleton bot instance.
    
    Returns:
        Optional[DiscordBot]: The bot instance or None if not started
    """
    return _bot_instance


async def start_bot() -> DiscordBot:
    """
    Start the Discord bot as a singleton.
    
    This should be called during application startup.
    
    Returns:
        DiscordBot: The bot instance
    
    Raises:
        RuntimeError: If bot is already running
    """
    global _bot_instance, _bot_task
    
    if _bot_instance is not None:
        raise RuntimeError("Bot is already running")
    
    logger.info("Starting Discord bot...")
    
    # Create bot instance
    _bot_instance = DiscordBot()
    
    # Start bot in background task
    _bot_task = asyncio.create_task(_run_bot())
    
    # Wait a moment for the bot to start
    await asyncio.sleep(1)
    
    return _bot_instance


async def _run_bot() -> None:
    """
    Internal function to run the bot.
    
    This runs in a background task.
    """
    global _bot_instance
    
    try:
        if _bot_instance:
            await _bot_instance.start(settings.DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error("Bot encountered an error: %s", e, exc_info=True)
        _bot_instance = None
        raise


async def stop_bot() -> None:
    """
    Stop the Discord bot.
    
    This should be called during application shutdown.
    """
    global _bot_instance, _bot_task
    
    if _bot_instance is None:
        logger.warning("Attempted to stop bot, but no bot is running")
        return
    
    logger.info("Stopping Discord bot...")
    
    try:
        # Close the bot connection
        await _bot_instance.close()
        
        # Cancel the background task if it exists
        if _bot_task and not _bot_task.done():
            _bot_task.cancel()
            try:
                await _bot_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Discord bot stopped successfully")
    
    except Exception as e:
        logger.error("Error stopping bot: %s", e, exc_info=True)
    
    finally:
        _bot_instance = None
        _bot_task = None
