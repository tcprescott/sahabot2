"""
Discord bot commands for Super Metroid randomizers.

Commands for generating SM seeds (VARIA, DASH, multiworld) via Discord.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from application.services.randomizer.sm_service import SMService

logger = logging.getLogger(__name__)


class SMCommands(commands.Cog):
    """Commands for Super Metroid randomizers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sm_service = SMService()

    async def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("SMCommands cog loaded")

    async def cog_unload(self):
        """Called when the cog is unloaded."""
        logger.info("SMCommands cog unloaded")

    @app_commands.command(
        name="smvaria",
        description="Generate a Super Metroid VARIA seed"
    )
    @app_commands.describe(
        preset="Preset name (optional, default: standard)",
        spoilers="Generate spoiler log (default: False)"
    )
    async def smvaria(
        self,
        interaction: discord.Interaction,
        preset: Optional[str] = "standard",
        spoilers: bool = False
    ):
        """
        Generate a Super Metroid VARIA seed.

        Args:
            interaction: Discord interaction
            preset: Preset name to use
            spoilers: Whether to generate spoiler log
        """
        await interaction.response.defer()

        try:
            # TODO: Load preset from database when preset system is integrated
            # For now, use basic default settings
            settings = {
                'preset': preset,
                'logic': 'casual',
                'itemProgression': 'normal',
                'morphPlacement': 'early',
            }

            logger.info(
                "Generating VARIA seed for user %s with preset %s",
                interaction.user.id,
                preset
            )

            result = await self.sm_service.generate_varia(
                settings=settings,
                tournament=False,  # Discord seeds are not race mode by default
                spoilers=spoilers
            )

            # Create embed with seed information
            embed = discord.Embed(
                title="Super Metroid VARIA Seed",
                description=f"Seed generated successfully!",
                color=discord.Color.green()
            )
            embed.add_field(name="Seed URL", value=result.url, inline=False)
            embed.add_field(name="Hash", value=result.hash_id, inline=True)
            embed.add_field(name="Preset", value=preset, inline=True)

            if spoilers and result.spoiler_url:
                embed.add_field(
                    name="Spoiler Log",
                    value=f"[View Spoiler]({result.spoiler_url})",
                    inline=False
                )

            embed.set_footer(text="Super Metroid VARIA Randomizer")

            await interaction.followup.send(embed=embed)

            logger.info("VARIA seed generated successfully: %s", result.hash_id)

        except Exception as e:
            logger.error("Failed to generate VARIA seed: %s", str(e), exc_info=True)
            await interaction.followup.send(
                f"❌ Failed to generate VARIA seed: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="smdash",
        description="Generate a Super Metroid DASH seed"
    )
    @app_commands.describe(
        preset="Preset name (optional, default: standard)",
        area_rando="Enable area randomization (default: False)",
        spoilers="Generate spoiler log (default: False)"
    )
    async def smdash(
        self,
        interaction: discord.Interaction,
        preset: Optional[str] = "standard",
        area_rando: bool = False,
        spoilers: bool = False
    ):
        """
        Generate a Super Metroid DASH seed.

        Args:
            interaction: Discord interaction
            preset: Preset name to use
            area_rando: Enable area randomization
            spoilers: Whether to generate spoiler log
        """
        await interaction.response.defer()

        try:
            # TODO: Load preset from database when preset system is integrated
            # For now, use basic default settings
            settings = {
                'preset': preset,
                'area_rando': area_rando,
                'major_minor_split': True,
            }

            logger.info(
                "Generating DASH seed for user %s with preset %s",
                interaction.user.id,
                preset
            )

            result = await self.sm_service.generate_dash(
                settings=settings,
                tournament=False,  # Discord seeds are not race mode by default
                spoilers=spoilers
            )

            # Create embed with seed information
            embed = discord.Embed(
                title="Super Metroid DASH Seed",
                description=f"Seed generated successfully!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Seed URL", value=result.url, inline=False)
            embed.add_field(name="Hash", value=result.hash_id, inline=True)
            embed.add_field(name="Preset", value=preset, inline=True)
            embed.add_field(
                name="Area Rando",
                value="Enabled" if area_rando else "Disabled",
                inline=True
            )

            if spoilers and result.spoiler_url:
                embed.add_field(
                    name="Spoiler Log",
                    value=f"[View Spoiler]({result.spoiler_url})",
                    inline=False
                )

            embed.set_footer(text="Super Metroid DASH Randomizer")

            await interaction.followup.send(embed=embed)

            logger.info("DASH seed generated successfully: %s", result.hash_id)

        except Exception as e:
            logger.error("Failed to generate DASH seed: %s", str(e), exc_info=True)
            await interaction.followup.send(
                f"❌ Failed to generate DASH seed: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="smtotal",
        description="Generate a Super Metroid total randomization seed"
    )
    @app_commands.describe(
        preset="Preset name (optional, default: total)",
        spoilers="Generate spoiler log (default: False)"
    )
    async def smtotal(
        self,
        interaction: discord.Interaction,
        preset: Optional[str] = "total",
        spoilers: bool = False
    ):
        """
        Generate a Super Metroid total randomization seed.

        Args:
            interaction: Discord interaction
            preset: Preset name to use
            spoilers: Whether to generate spoiler log
        """
        await interaction.response.defer()

        try:
            # Total randomization with all features enabled
            settings = {
                'preset': preset,
                'area_rando': True,
                'major_minor_split': True,
                'boss_rando': True,
            }

            logger.info(
                "Generating total randomization seed for user %s",
                interaction.user.id
            )

            result = await self.sm_service.generate(
                settings=settings,
                randomizer_type='total',
                tournament=False,
                spoilers=spoilers
            )

            # Create embed with seed information
            embed = discord.Embed(
                title="Super Metroid Total Randomization Seed",
                description=f"Seed with full randomization generated!",
                color=discord.Color.purple()
            )
            embed.add_field(name="Seed URL", value=result.url, inline=False)
            embed.add_field(name="Hash", value=result.hash_id, inline=True)
            embed.add_field(name="Preset", value=preset, inline=True)
            embed.add_field(name="Features", value="Area + Boss + Major/Minor Split", inline=False)

            if spoilers and result.spoiler_url:
                embed.add_field(
                    name="Spoiler Log",
                    value=f"[View Spoiler]({result.spoiler_url})",
                    inline=False
                )

            embed.set_footer(text="Super Metroid Total Randomization")

            await interaction.followup.send(embed=embed)

            logger.info("Total randomization seed generated: %s", result.hash_id)

        except Exception as e:
            logger.error("Failed to generate total seed: %s", str(e), exc_info=True)
            await interaction.followup.send(
                f"❌ Failed to generate total randomization seed: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function to add the cog."""
    await bot.add_cog(SMCommands(bot))
    logger.info("SMCommands cog added")
