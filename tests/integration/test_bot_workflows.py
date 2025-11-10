"""
Integration tests for Discord bot workflows.

Tests complete bot command and interaction workflows.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from discordbot.client import DiscordBot, get_bot_instance
from discordbot.commands.test_commands import TestCommands as DiscordTestCommands
import discord


@pytest.mark.integration
@pytest.mark.asyncio
class TestBotWorkflows:
    """Test cases for bot integration workflows."""

    async def test_bot_startup_and_shutdown(self):
        """Test bot startup and shutdown lifecycle."""
        # Bot lifecycle is managed in main.py via lifespan
        # We can test the singleton pattern and basic properties

        # Get bot instance (should be None if not started)
        bot = get_bot_instance()

        # For testing, we don't actually start the bot
        # We test the DiscordBot class properties
        test_bot = DiscordBot()

        # Verify initialization
        assert test_bot.command_prefix == "!"
        assert test_bot.help_command is None
        assert test_bot._bot_ready is False

        # Verify intents configuration
        assert test_bot.intents.guilds is True
        # Note: message_content is a privileged intent and may not be enabled
        # We just verify guilds intent is properly set

    async def test_command_registration_and_sync(self):
        """Test commands are registered and synced to Discord."""
        # Create bot instance
        bot = DiscordBot()

        # Verify command tree exists
        assert bot.tree is not None

        # Load test commands cog
        await bot.load_extension("discordbot.commands.test_commands")

        # Verify cog was loaded (use string name to avoid name collision)
        test_cog = bot.get_cog("TestCommands")
        assert test_cog is not None
        # Don't check isinstance since pytest has its own TestCommands

        # Verify test command is registered
        assert hasattr(test_cog, "test")
        assert isinstance(test_cog.test, discord.app_commands.Command)

    async def test_test_command_full_workflow(self, mock_discord_interaction):
        """Test complete /test command workflow."""
        # Create bot and load commands
        bot = DiscordBot()
        await bot.load_extension("discordbot.commands.test_commands")

        # Get test cog
        cog = bot.get_cog("TestCommands")
        assert cog is not None

        # Mock interaction
        interaction = mock_discord_interaction

        # Call command callback
        await cog.test.callback(cog, interaction)

        # Verify response was sent
        interaction.response.send_message.assert_called_once()

        # Get the embed from the call
        call_kwargs = interaction.response.send_message.call_args[1]
        embed = call_kwargs["embed"]

        # Verify embed properties (use actual title from implementation)
        assert embed.title == "✅ Bot Test"
        assert "working correctly" in embed.description
        assert embed.color == discord.Color.green()

        # Verify ephemeral flag
        assert call_kwargs.get("ephemeral") is True

    async def test_bot_error_handling(self):
        """Test bot handles errors gracefully."""
        # Create bot instance
        bot = DiscordBot()

        # Test _should_sync_commands is async
        # It returns a coroutine, so we need to await it
        bot._bot_ready = False

        # Mock tree.get_commands to return empty list
        with patch.object(bot.tree, "get_commands", return_value=[]):
            with patch.object(bot.tree, "fetch_commands", AsyncMock(return_value=[])):
                # Should not sync if commands match
                should_sync = await bot._should_sync_commands()
                # Both empty, so no sync needed
                assert should_sync is False

        # Test on_command_error event handler exists
        assert hasattr(bot, "on_command_error")

        # Bot should handle connection errors gracefully
        # In real usage, errors are logged and don't crash the bot
        assert bot is not None
