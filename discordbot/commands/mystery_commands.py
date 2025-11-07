"""
Discord bot commands for ALTTPR mystery seed generation.
"""

import logging
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class MysteryCommands(commands.Cog):
    """Cog for ALTTPR mystery seed generation commands."""

    def __init__(self, bot: commands.Bot):
        """
        Initialize the mystery commands cog.

        Args:
            bot: Discord bot instance
        """
        self.bot = bot

    @app_commands.command(name="mystery", description="Generate an ALTTPR mystery seed from a preset")
    @app_commands.describe(
        preset_name="Name of the mystery preset to use"
    )
    async def mystery_command(self, interaction: discord.Interaction, preset_name: str):
        """
        Generate an ALTTPR mystery seed from a named preset.

        Public presets can be accessed by anyone (no authentication required).
        Private presets require authentication and ownership.

        Args:
            interaction: Discord interaction
            preset_name: Name of the mystery preset
        """
        await interaction.response.defer(ephemeral=False)

        try:
            from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService
            from models import User

            # Get user from database (optional for public presets)
            user = await User.get_or_none(discord_id=str(interaction.user.id))
            user_id = user.id if user else None

            # Generate mystery seed
            service = ALTTPRMysteryService()
            result, description = await service.generate_from_preset_name(
                mystery_preset_name=preset_name,
                user_id=user_id,
                tournament=True,
                spoilers='off'
            )

            # Format description
            desc_parts = []
            if 'preset' in description:
                desc_parts.append(f"**Preset:** {description['preset']}")
            if 'subweight' in description:
                desc_parts.append(f"**Subweight:** {description['subweight']}")
            if 'entrance' in description and description['entrance'] != 'none':
                desc_parts.append(f"**Entrance:** {description['entrance']}")
            if 'customizer' in description:
                desc_parts.append("**Customizer:** enabled")

            # Create embed
            embed = discord.Embed(
                title="🎲 Mystery Seed Generated",
                description=f"Mystery preset: **{preset_name}**",
                color=discord.Color.purple()
            )

            embed.add_field(name="Seed URL", value=result.url, inline=False)
            embed.add_field(name="Hash", value=result.hash_id, inline=True)

            if desc_parts:
                embed.add_field(name="Rolled Settings", value="\n".join(desc_parts), inline=False)

            embed.set_footer(text=f"Requested by {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

            logger.info(
                "Generated mystery seed for user %s with preset %s: %s",
                user.id, preset_name, result.hash_id
            )

        except ValueError as e:
            logger.error("Mystery generation error: %s", str(e))
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )
        except PermissionError as e:
            logger.error("Mystery permission error: %s", str(e))
            await interaction.followup.send(
                f"❌ {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logger.exception("Unexpected error generating mystery seed")
            await interaction.followup.send(
                f"❌ An unexpected error occurred: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="mysterylist", description="List available ALTTPR mystery presets")
    async def mystery_list_command(self, interaction: discord.Interaction):
        """
        List available mystery presets.

        Args:
            interaction: Discord interaction
        """
        await interaction.response.defer(ephemeral=True)

        try:
            from application.repositories.randomizer_preset_repository import RandomizerPresetRepository

            # Get all public mystery presets
            preset_repo = RandomizerPresetRepository()
            presets = await preset_repo.list_public_presets(randomizer='alttpr')

            # Filter for mystery presets using the same logic as _is_mystery_preset
            mystery_presets = []
            for p in presets:
                # Check if explicit mystery type
                if p.settings.get('preset_type') == 'mystery':
                    mystery_presets.append(p)
                # Check if has weights or mystery_weights
                elif 'weights' in p.settings or 'mystery_weights' in p.settings:
                    mystery_presets.append(p)
                # Check in 'settings' sub-dict (SahasrahBot format)
                elif 'settings' in p.settings:
                    settings = p.settings.get('settings')
                    if isinstance(settings, dict):
                        if 'weights' in settings or 'mystery_weights' in settings:
                            mystery_presets.append(p)

            if not mystery_presets:
                await interaction.followup.send(
                    "No public mystery presets available.",
                    ephemeral=True
                )
                return

            # Create embed
            embed = discord.Embed(
                title="🎲 Available Mystery Presets",
                description=f"Found {len(mystery_presets)} mystery preset(s)",
                color=discord.Color.purple()
            )

            # Add presets to embed (limit to 25 fields)
            for preset in mystery_presets[:25]:
                description = preset.description or "No description"
                embed.add_field(
                    name=preset.name,
                    value=description[:100],  # Truncate long descriptions
                    inline=False
                )

            if len(mystery_presets) > 25:
                embed.set_footer(text=f"Showing first 25 of {len(mystery_presets)} presets")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Error listing mystery presets")
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """
    Setup function for loading the cog.

    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(MysteryCommands(bot))
    logger.info("Mystery commands cog loaded")
