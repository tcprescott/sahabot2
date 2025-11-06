"""
Discord bot commands for SMZ3 randomizer.

Admin commands for generating SMZ3 seeds via Discord.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from application.services.randomizer.smz3_service import SMZ3Service, DEFAULT_SMZ3_SETTINGS
from application.services.randomizer.randomizer_preset_service import RandomizerPresetService

logger = logging.getLogger(__name__)


class SMZ3Commands(commands.Cog):
    """Commands for SMZ3 randomizer seed generation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.smz3_service = SMZ3Service()
        self.preset_service = RandomizerPresetService()

    async def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("SMZ3Commands cog loaded")

    async def cog_unload(self):
        """Called when the cog is unloaded."""
        logger.info("SMZ3Commands cog unloaded")

    @app_commands.command(
        name="smz3",
        description="Generate an SMZ3 (Super Metroid + ALTTP Combo) randomizer seed"
    )
    @app_commands.describe(
        preset="Optional preset name to use for seed generation",
        spoiler="Generate seed with spoiler log (default: False)"
    )
    async def smz3_generate(
        self,
        interaction: discord.Interaction,
        preset: Optional[str] = None,
        spoiler: bool = False
    ):
        """Generate an SMZ3 randomizer seed."""
        await interaction.response.defer(thinking=True)

        try:
            # Start with default settings
            settings = DEFAULT_SMZ3_SETTINGS.copy()

            # Load preset if specified
            preset_info = ""
            if preset:
                try:
                    preset_obj = await self.preset_service.get_preset_by_name(
                        randomizer='smz3',
                        name=preset
                    )
                    if preset_obj and preset_obj.settings:
                        settings.update(preset_obj.settings)
                        preset_info = f"Preset: {preset}\n"
                        logger.info("Loaded SMZ3 preset: %s", preset)
                    else:
                        preset_info = f"Warning: Preset '{preset}' not found, using defaults\n"
                except Exception as e:
                    logger.error("Error loading preset %s: %s", preset, e)
                    preset_info = f"Warning: Could not load preset '{preset}', using defaults\n"

            # Generate seed
            spoiler_key = "spoiler" if spoiler else None
            result = await self.smz3_service.generate(
                settings=settings,
                tournament=not spoiler,  # Tournament mode unless spoiler requested
                spoilers=spoiler,
                spoiler_key=spoiler_key
            )

            # Create embed with seed info
            embed = discord.Embed(
                title="🎮 SMZ3 Seed Generated",
                description="Super Metroid + A Link to the Past Combo Randomizer",
                color=discord.Color.green()
            )

            # Add seed URL
            embed.add_field(
                name="Seed URL",
                value=result.url,
                inline=False
            )

            # Add preset info if used
            if preset_info:
                embed.add_field(
                    name="Settings",
                    value=preset_info.strip(),
                    inline=False
                )

            # Add spoiler URL if generated
            if spoiler and result.spoiler_url:
                embed.add_field(
                    name="Spoiler Log",
                    value=result.spoiler_url,
                    inline=False
                )

            # Add seed details from metadata
            if result.metadata:
                details = []
                if 'logic' in settings:
                    details.append(f"Logic: {settings['logic']}")
                if 'mode' in settings:
                    details.append(f"Mode: {settings['mode']}")
                if 'goal' in settings:
                    details.append(f"Goal: {settings['goal']}")

                if details:
                    embed.add_field(
                        name="Configuration",
                        value=" | ".join(details),
                        inline=False
                    )

            embed.set_footer(text=f"Seed Hash: {result.hash_id}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error("Error generating SMZ3 seed: %s", e, exc_info=True)
            await interaction.followup.send(
                f"❌ Error generating SMZ3 seed: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="smz3_presets",
        description="List available SMZ3 presets"
    )
    async def smz3_presets(self, interaction: discord.Interaction):
        """List available SMZ3 presets."""
        await interaction.response.defer(thinking=True)

        try:
            # Get all SMZ3 presets
            presets = await self.preset_service.list_presets(
                randomizer='smz3',
                is_public=True
            )

            if not presets:
                await interaction.followup.send(
                    "No SMZ3 presets available yet. Create one via the web interface!",
                    ephemeral=True
                )
                return

            # Create embed with preset list
            embed = discord.Embed(
                title="📋 Available SMZ3 Presets",
                description=f"Found {len(presets)} public SMZ3 preset(s)",
                color=discord.Color.blue()
            )

            # Add presets (limit to first 25 due to Discord embed field limits)
            for preset in presets[:25]:
                description = preset.description or "No description"
                embed.add_field(
                    name=preset.name,
                    value=description[:100],  # Limit description length
                    inline=False
                )

            if len(presets) > 25:
                embed.set_footer(text=f"Showing 25 of {len(presets)} presets")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error("Error listing SMZ3 presets: %s", e, exc_info=True)
            await interaction.followup.send(
                f"❌ Error listing presets: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function to add the cog."""
    await bot.add_cog(SMZ3Commands(bot))
    logger.info("SMZ3Commands cog added")
