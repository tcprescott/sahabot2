"""
Unit tests for Discord bot client.

Tests the bot client initialization and lifecycle.
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock, patch
from discordbot.client import DiscordBot, get_bot_instance


@pytest.mark.unit
@pytest.mark.asyncio
class TestDiscordBot:
    """Test cases for DiscordBot."""
    
    async def test_bot_initialization(self):
        """Test bot initializes with correct settings."""
        bot = DiscordBot()
        
        # Verify bot is a commands.Bot instance
        assert isinstance(bot, discord.ext.commands.Bot)
        
        # Verify command prefix
        assert bot.command_prefix == '!'
        
        # Verify help command is disabled (None)
        assert bot.help_command is None
        
        # Verify ready flag is initially False
        assert bot._bot_ready is False
    
    async def test_bot_intents_configuration(self):
        """Test bot has required intents."""
        bot = DiscordBot()
        
        # Verify intents are configured
        assert bot.intents is not None
        
        # Verify guilds intent is enabled
        assert bot.intents.guilds is True
        
        # Verify it's based on default intents
        default_intents = discord.Intents.default()
        assert bot.intents.value & default_intents.value == default_intents.value
    
    async def test_on_ready_event(self):
        """Test on_ready event handler."""
        bot = DiscordBot()
        
        # Mock user and guilds by patching the base class properties
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.__str__ = MagicMock(return_value="TestBot#0001")
        
        mock_guild1 = MagicMock()
        mock_guild2 = MagicMock()
        
        # Mock change_presence
        bot.change_presence = AsyncMock()
        
        # Directly set internal attributes (not properties)
        bot._connection = MagicMock()
        bot._connection.user = mock_user
        bot._connection._guilds = {1: mock_guild1, 2: mock_guild2}
        
        # Call on_ready
        await bot.on_ready()
        
        # Verify ready flag is set
        assert bot._bot_ready is True
        
        # Verify is_ready property (requires not closed)
        with patch.object(bot, 'is_closed', return_value=False):
            assert bot.is_ready is True
        
        # Verify presence was set
        bot.change_presence.assert_called_once()
        call_args = bot.change_presence.call_args
        activity = call_args.kwargs['activity']
        assert activity.type == discord.ActivityType.watching
        assert activity.name == "for commands"
    
    async def test_singleton_pattern(self):
        """Test bot uses singleton pattern correctly."""
        # Initially, no bot instance exists
        from discordbot.client import _bot_instance
        initial_instance = _bot_instance
        
        # get_bot_instance should return the current instance (None or existing)
        current = get_bot_instance()
        assert current == initial_instance
