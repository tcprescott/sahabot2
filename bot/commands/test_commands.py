"""
Test commands for the Discord bot.

This module contains simple test commands to verify bot functionality.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)


class TestCommands(commands.Cog):
    """Test commands cog for basic bot functionality testing."""
    
    def __init__(self, bot: commands.Bot):
        """
        Initialize the test commands cog.
        
        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
    
    @app_commands.command(name="test", description="Test command to verify bot is working")
    async def test(self, interaction: discord.Interaction):
        """
        Simple test command that responds with a confirmation message.
        
        Args:
            interaction: The Discord interaction object
        """
        logger.info(f"Test command invoked by {interaction.user} (ID: {interaction.user.id})")
        
        # Create an embed for a nice-looking response
        embed = discord.Embed(
            title="✅ Bot Test",
            description="The bot is working correctly!",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=interaction.user.mention, inline=True)
        embed.add_field(name="User ID", value=str(interaction.user.id), inline=True)
        embed.set_footer(text="SahaBot2")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info("Test command completed successfully")


async def setup(bot: commands.Bot):
    """
    Setup function to add the test commands cog to the bot.
    
    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(TestCommands(bot))
    logger.info("Test commands cog loaded")
