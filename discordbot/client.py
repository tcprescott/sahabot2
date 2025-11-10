"""
Discord bot client for SahaBot2.

This module provides a singleton Discord bot that runs within the application.
"""

import discord
from discord.ext import commands
import asyncio
import hashlib
import json
import logging
from typing import Optional
from config import settings
import sentry_sdk

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
        # Configure intents (avoid privileged intents when possible)
        intents = discord.Intents.default()
        intents.guilds = True  # Explicitly enable guild events
        # Note: members intent is privileged and not required for basic functionality

        # Initialize bot
        super().__init__(
            command_prefix="!",  # Default prefix, can be changed later
            intents=intents,
            help_command=None,  # We'll implement custom help if needed
        )

        self._bot_ready = False  # Custom ready flag (don't shadow discord.py's _ready)

    async def _should_sync_commands(self) -> bool:
        """
        Determine if command sync is needed.

        Compares local commands with Discord's registered commands to avoid
        unnecessary sync operations.

        Returns:
            bool: True if sync is needed, False otherwise
        """
        try:
            # Get current local commands
            local_commands = self.tree.get_commands()

            # Create a signature of local commands (name, description, options)
            local_signature = self._create_command_signature(local_commands)

            # Fetch currently registered commands from Discord
            try:
                registered_commands = await self.tree.fetch_commands()
            except discord.HTTPException as e:
                # If we can't fetch, assume we need to sync
                logger.warning("Could not fetch registered commands: %s, will sync", e)
                return True

            # Create signature of registered commands
            registered_signature = self._create_command_signature(registered_commands)

            # Compare signatures
            if local_signature != registered_signature:
                logger.info(
                    "Command changes detected (local: %d, registered: %d)",
                    len(local_commands),
                    len(registered_commands),
                )
                logger.debug("Local signature: %s", local_signature)
                logger.debug("Registered signature: %s", registered_signature)
                return True

            logger.info("Commands already in sync, skipping sync")
            return False

        except Exception as e:
            # On error, be safe and sync
            logger.warning("Error checking if sync needed: %s, will sync", e)
            return True

    def _create_command_signature(self, command_list: list) -> str:
        """
        Create a signature hash of commands for comparison.

        Args:
            command_list: List of Discord commands (either app_commands.Command or fetched)

        Returns:
            str: SHA256 hash of command signatures
        """
        signature_data = []

        for cmd in sorted(command_list, key=lambda c: c.name):
            cmd_data = {
                "name": cmd.name,
                "description": cmd.description or "",  # Normalize None to empty string
                "options": [],
            }

            # Handle both Command objects and fetched AppCommand objects
            # Command objects have 'parameters', AppCommand objects have 'options'
            params = []
            if hasattr(cmd, "parameters"):
                params = cmd.parameters
            elif hasattr(cmd, "options"):
                params = cmd.options

            for param in params:
                param_data = {
                    "name": param.name,
                    "description": param.description or "",  # Normalize None
                    "required": getattr(param, "required", False),
                }
                cmd_data["options"].append(param_data)

            # Sort options by name for consistency
            cmd_data["options"] = sorted(cmd_data["options"], key=lambda x: x["name"])

            signature_data.append(cmd_data)

        # Create deterministic JSON and hash it
        signature_json = json.dumps(signature_data, sort_keys=True)
        signature_hash = hashlib.sha256(signature_json.encode()).hexdigest()

        logger.debug(
            "Created signature for %d commands: %s",
            len(command_list),
            signature_hash[:16],
        )

        return signature_hash

    async def setup_hook(self) -> None:
        """
        Setup hook called when the bot is starting up.

        This is where we'll load cogs/extensions.
        """
        logger.info("Bot setup hook called")

        # Load command cogs
        try:
            await self.load_extension("discordbot.commands.test_commands")
            logger.info("Loaded test commands")
        except Exception as e:
            logger.error("Failed to load test commands: %s", e, exc_info=True)

        # Load async tournament cog
        try:
            await self.load_extension("discordbot.commands.async_tournament")
            logger.info("Loaded async tournament commands")
        except Exception as e:
            logger.error(
                "Failed to load async tournament commands: %s", e, exc_info=True
            )

        # Load SM randomizer cog
        try:
            await self.load_extension("discordbot.commands.sm_commands")
            logger.info("Loaded SM randomizer commands")
        except Exception as e:
            logger.error("Failed to load SM randomizer commands: %s", e, exc_info=True)
        # Load SMZ3 randomizer cog
        try:
            await self.load_extension("discordbot.commands.smz3")
            logger.info("Loaded SMZ3 commands")
        except Exception as e:
            logger.error("Failed to load SMZ3 commands: %s", e, exc_info=True)

        # Load mystery commands
        try:
            await self.load_extension("discordbot.commands.mystery_commands")
            logger.info("Loaded mystery commands")
        except Exception as e:
            logger.error("Failed to load mystery commands: %s", e, exc_info=True)

        # Smart sync commands to Discord
        try:
            if await self._should_sync_commands():
                logger.info("Syncing commands to Discord...")
                synced = await self.tree.sync()
                logger.info("Synced %d command(s) to Discord", len(synced))
            else:
                logger.info("Commands already in sync with Discord")
        except Exception as e:
            logger.error("Failed to sync commands: %s", e, exc_info=True)

    async def on_ready(self) -> None:
        """Event handler called when the bot is ready."""
        self._bot_ready = True
        logger.info("Bot is ready! Logged in as %s (ID: %s)", self.user, self.user.id)
        logger.info("Connected to %d guilds", len(self.guilds))

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="for commands"
            )
        )

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """
        Event handler for bot errors.

        Args:
            event_method: The event method that raised the error
        """
        logger.error("Error in %s", event_method, exc_info=True)
        # Capture exception in Sentry
        sentry_sdk.capture_exception()

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """
        Event handler for command errors.

        Args:
            ctx: Command context
            error: The error that occurred
        """
        logger.error("Command error in %s: %s", ctx.command, error, exc_info=error)
        # Capture exception in Sentry with additional context
        with sentry_sdk.push_scope() as scope:
            scope.set_context(
                "discord_command",
                {
                    "command": str(ctx.command),
                    "author": str(ctx.author),
                    "guild": str(ctx.guild) if ctx.guild else None,
                    "channel": str(ctx.channel),
                },
            )
            sentry_sdk.capture_exception(error)

    @property
    def is_ready(self) -> bool:
        """
        Check if the bot is ready.

        Returns:
            bool: True if bot is connected and ready
        """
        return self._bot_ready and not self.is_closed()


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
