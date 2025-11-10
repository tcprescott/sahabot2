"""
Unit tests for Discord bot commands.

Tests the bot command functionality.
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock
from discordbot.commands.test_commands import TestCommands


@pytest.mark.unit
@pytest.mark.asyncio
class TestBotTestCommands:
    """Test cases for bot test commands."""

    async def test_test_command_response(self):
        """Test /test command returns correct response."""
        # Create mock bot and cog
        mock_bot = MagicMock()
        cog = TestCommands(mock_bot)

        # Create mock interaction
        mock_interaction = AsyncMock(spec=discord.Interaction)
        mock_user = MagicMock()
        mock_user.mention = "<@123456789>"
        mock_user.id = 123456789
        mock_user.__str__ = MagicMock(return_value="TestUser#0001")
        mock_interaction.user = mock_user
        mock_interaction.response = AsyncMock()

        # Call the command callback directly
        await cog.test.callback(cog, mock_interaction)

        # Verify response was sent
        mock_interaction.response.send_message.assert_called_once()

        # Get the call arguments
        call_args = mock_interaction.response.send_message.call_args

        # Verify embed was sent
        assert "embed" in call_args.kwargs
        embed = call_args.kwargs["embed"]
        assert isinstance(embed, discord.Embed)

        # Verify embed content
        assert embed.title == "✅ Bot Test"
        assert "working correctly" in embed.description
        assert embed.color == discord.Color.green()

    async def test_test_command_ephemeral(self):
        """Test /test command response is ephemeral."""
        # Create mock bot and cog
        mock_bot = MagicMock()
        cog = TestCommands(mock_bot)

        # Create mock interaction
        mock_interaction = AsyncMock(spec=discord.Interaction)
        mock_user = MagicMock()
        mock_user.mention = "<@123456789>"
        mock_user.id = 123456789
        mock_user.__str__ = MagicMock(return_value="TestUser#0001")
        mock_interaction.user = mock_user
        mock_interaction.response = AsyncMock()

        # Call the command callback directly
        await cog.test.callback(cog, mock_interaction)

        # Verify ephemeral=True
        call_args = mock_interaction.response.send_message.call_args
        assert call_args.kwargs.get("ephemeral") is True

    async def test_test_command_embed_format(self):
        """Test /test command response embed format."""
        # Create mock bot and cog
        mock_bot = MagicMock()
        cog = TestCommands(mock_bot)

        # Create mock interaction
        mock_interaction = AsyncMock(spec=discord.Interaction)
        mock_user = MagicMock()
        mock_user.mention = "<@987654321>"
        mock_user.id = 987654321
        mock_user.__str__ = MagicMock(return_value="AnotherUser#0002")
        mock_interaction.user = mock_user
        mock_interaction.response = AsyncMock()

        # Call the command callback directly
        await cog.test.callback(cog, mock_interaction)

        # Get the embed
        call_args = mock_interaction.response.send_message.call_args
        embed = call_args.kwargs["embed"]

        # Verify embed has required fields
        assert len(embed.fields) >= 2

        # Find User and User ID fields
        field_names = [field.name for field in embed.fields]
        assert "User" in field_names
        assert "User ID" in field_names

        # Verify field values
        user_field = next(f for f in embed.fields if f.name == "User")
        user_id_field = next(f for f in embed.fields if f.name == "User ID")

        assert user_field.value == "<@987654321>"
        assert user_id_field.value == "987654321"

        # Verify footer
        assert embed.footer is not None
        assert embed.footer.text == "SahaBot2"
