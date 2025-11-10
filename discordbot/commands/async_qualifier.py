"""
Discord bot commands for async qualifier management.

Admin commands for managing async qualifiers via Discord.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta, timezone

from models import User
from models.async_tournament import AsyncQualifier, AsyncQualifierRace
from application.services.tournaments.async_qualifier_service import (
    AsyncQualifierService,
)
from discordbot.async_qualifier_views import AsyncQualifierMainView

logger = logging.getLogger(__name__)


class AsyncQualifierCommands(commands.Cog):
    """Admin commands for async qualifiers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service = AsyncQualifierService()
        self._views_added = False

    async def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("AsyncQualifierCommands cog loaded")

    async def cog_unload(self):
        """Called when the cog is unloaded."""
        logger.info("AsyncQualifierCommands cog unloaded")

    @commands.Cog.listener()
    async def on_ready(self):
        """Add persistent views when bot is ready."""
        if not self._views_added:
            self.bot.add_view(AsyncQualifierMainView())
            from discordbot.async_qualifier_views import (
                RaceReadyView,
                RaceInProgressView,
                RaceCompletedView,
            )

            self.bot.add_view(RaceReadyView())
            self.bot.add_view(RaceInProgressView())
            self.bot.add_view(RaceCompletedView())
            self._views_added = True
            logger.info("Added persistent async qualifier views")

    @app_commands.command(
        name="async_post_embed",
        description="Post the async qualifier embed in this channel",
    )
    @app_commands.default_permissions(administrator=True)
    async def post_embed(self, interaction: discord.Interaction):
        """Post the async qualifier embed with action buttons."""
        qualifier = await AsyncQualifier.get_or_none(
            discord_channel_id=interaction.channel_id
        )

        if not qualifier:
            await interaction.response.send_message(
                "This channel is not configured for async qualifiers. "
                "Please configure it via the web interface first.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=tournament.name,
            description=tournament.description or "Async Tournament",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="How to Participate",
            value="Click 'Start New Async Run' below to begin a new race.",
            inline=False,
        )
        embed.add_field(
            name="Status",
            value="Active" if qualifier.is_active else "Inactive",
            inline=True,
        )
        embed.add_field(
            name="Runs Per Pool", value=str(tournament.runs_per_pool), inline=True
        )
        embed.set_footer(text=f"Tournament ID: {tournament.id}")

        await interaction.response.send_message(
            embed=embed, view=AsyncQualifierMainView()
        )

    @app_commands.command(
        name="async_extend_timeout",
        description="Extend the timeout for a race in this thread",
    )
    @app_commands.describe(minutes="Number of minutes to extend")
    async def extend_timeout(self, interaction: discord.Interaction, minutes: int):
        """Extend the timeout for a pending race."""
        race = await AsyncQualifierRace.get_or_none(
            discord_thread_id=interaction.channel_id
        ).prefetch_related("tournament")

        if not race:
            await interaction.response.send_message(
                "This is not a valid race thread.", ephemeral=True
            )
            return

        if race.status != "pending":
            await interaction.response.send_message(
                "Can only extend timeout for pending races.", ephemeral=True
            )
            return

        # Check if user can manage tournaments
        user = await User.get_or_none(discord_id=interaction.user.id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return

        can_manage = await self.service.can_manage_async_tournaments(
            user, race.tournament.organization_id
        )
        if not can_manage:
            await interaction.response.send_message(
                "You don't have permission to manage this qualifier.", ephemeral=True
            )
            return

        # Extend timeout
        if race.thread_timeout_time:
            new_timeout = race.thread_timeout_time + timedelta(minutes=minutes)
        else:
            base_time = race.thread_open_time or datetime.now(timezone.utc)
            new_timeout = base_time + timedelta(minutes=20 + minutes)

        race.thread_timeout_time = new_timeout
        await race.save()

        await self.service.repo.create_audit_log(
            tournament_id=race.tournament_id,
            action="extend_timeout",
            details=f"Race {race.id} timeout extended by {minutes} minutes",
            user_id=user.id,
        )

        await interaction.response.send_message(
            f"Timeout extended to {discord.utils.format_dt(new_timeout, 'f')} "
            f"({discord.utils.format_dt(new_timeout, 'R')})"
        )

    @app_commands.command(
        name="async_calculate_scores",
        description="Recalculate scores for this tournament",
    )
    async def calculate_scores(self, interaction: discord.Interaction):
        """Manually trigger score calculation."""
        qualifier = await AsyncQualifier.get_or_none(
            discord_channel_id=interaction.channel_id
        )

        if not qualifier:
            await interaction.response.send_message(
                "This channel is not configured for async qualifiers.", ephemeral=True
            )
            return

        user = await User.get_or_none(discord_id=interaction.user.id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return

        can_manage = await self.service.can_manage_async_tournaments(
            user, qualifier.organization_id
        )
        if not can_manage:
            await interaction.response.send_message(
                "You don't have permission to manage this qualifier.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        success = await self.service.calculate_tournament_scores(
            user, qualifier.organization_id, qualifier.id
        )

        if success:
            await interaction.followup.send(
                "Scores recalculated successfully!", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Failed to recalculate scores.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function to add the cog."""
    await bot.add_cog(AsyncQualifierCommands(bot))
    logger.info("AsyncQualifierCommands cog added")
