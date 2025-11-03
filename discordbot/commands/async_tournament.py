"""
Discord bot commands for async tournament management.

Admin commands for managing async tournaments via Discord.
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta, timezone

from models import User
from models.async_tournament import AsyncTournament, AsyncTournamentRace
from application.services.async_tournament_service import AsyncTournamentService
from discordbot.async_tournament_views import AsyncTournamentMainView

logger = logging.getLogger(__name__)


class AsyncTournamentCommands(commands.Cog):
    """Admin commands for async tournaments."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service = AsyncTournamentService()
        self._views_added = False

        # Start background tasks
        self.timeout_pending_races.start()
        self.timeout_in_progress_races.start()
        self.score_calculation.start()

    async def cog_load(self):
        """Called when the cog is loaded."""
        logger.info("AsyncTournamentCommands cog loaded")

    async def cog_unload(self):
        """Called when the cog is unloaded."""
        self.timeout_pending_races.cancel()
        self.timeout_in_progress_races.cancel()
        self.score_calculation.cancel()
        logger.info("AsyncTournamentCommands cog unloaded")

    @commands.Cog.listener()
    async def on_ready(self):
        """Add persistent views when bot is ready."""
        if not self._views_added:
            self.bot.add_view(AsyncTournamentMainView())
            from discordbot.async_tournament_views import RaceReadyView, RaceInProgressView
            self.bot.add_view(RaceReadyView())
            self.bot.add_view(RaceInProgressView())
            self._views_added = True
            logger.info("Added persistent async tournament views")

    @app_commands.command(
        name="async_post_embed",
        description="Post the async tournament embed in this channel"
    )
    @app_commands.default_permissions(administrator=True)
    async def post_embed(self, interaction: discord.Interaction):
        """Post the async tournament embed with action buttons."""
        tournament = await AsyncTournament.get_or_none(discord_channel_id=interaction.channel_id)

        if not tournament:
            await interaction.response.send_message(
                "This channel is not configured for async tournaments. "
                "Please configure it via the web interface first.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=tournament.name,
            description=tournament.description or "Async Tournament",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="How to Participate",
            value="Click 'Start New Async Run' below to begin a new race.",
            inline=False
        )
        embed.add_field(
            name="Status",
            value="Active" if tournament.is_active else "Inactive",
            inline=True
        )
        embed.add_field(
            name="Runs Per Pool",
            value=str(tournament.runs_per_pool),
            inline=True
        )
        embed.set_footer(text=f"Tournament ID: {tournament.id}")

        await interaction.response.send_message(
            embed=embed,
            view=AsyncTournamentMainView()
        )

    @app_commands.command(
        name="async_extend_timeout",
        description="Extend the timeout for a race in this thread"
    )
    @app_commands.describe(minutes="Number of minutes to extend")
    async def extend_timeout(self, interaction: discord.Interaction, minutes: int):
        """Extend the timeout for a pending race."""
        race = await AsyncTournamentRace.get_or_none(
            discord_thread_id=interaction.channel_id
        ).prefetch_related('tournament')

        if not race:
            await interaction.response.send_message(
                "This is not a valid race thread.",
                ephemeral=True
            )
            return

        if race.status != 'pending':
            await interaction.response.send_message(
                "Can only extend timeout for pending races.",
                ephemeral=True
            )
            return

        # Check if user can manage tournaments
        user = await User.get_or_none(discord_id=interaction.user.id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return

        can_manage = await self.service.can_manage_async_tournaments(user, race.tournament.organization_id)
        if not can_manage:
            await interaction.response.send_message(
                "You don't have permission to manage this tournament.",
                ephemeral=True
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
        description="Recalculate scores for this tournament"
    )
    async def calculate_scores(self, interaction: discord.Interaction):
        """Manually trigger score calculation."""
        tournament = await AsyncTournament.get_or_none(discord_channel_id=interaction.channel_id)

        if not tournament:
            await interaction.response.send_message(
                "This channel is not configured for async tournaments.",
                ephemeral=True
            )
            return

        user = await User.get_or_none(discord_id=interaction.user.id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return

        can_manage = await self.service.can_manage_async_tournaments(user, tournament.organization_id)
        if not can_manage:
            await interaction.response.send_message(
                "You don't have permission to manage this tournament.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        success = await self.service.calculate_tournament_scores(
            user, tournament.organization_id, tournament.id
        )

        if success:
            await interaction.followup.send("Scores recalculated successfully!", ephemeral=True)
        else:
            await interaction.followup.send("Failed to recalculate scores.", ephemeral=True)

    # Background tasks

    @tasks.loop(seconds=60)
    async def timeout_pending_races(self):
        """Background task to timeout pending races."""
        try:
            pending_races = await AsyncTournamentRace.filter(
                status='pending',
                discord_thread_id__isnull=False
            ).prefetch_related('user')

            for race in pending_races:
                # Set default timeout if not set
                if not race.thread_timeout_time:
                    if race.thread_open_time:
                        race.thread_timeout_time = race.thread_open_time + timedelta(minutes=20)
                        await race.save()

                if not race.thread_timeout_time:
                    continue

                warning_time = race.thread_timeout_time - timedelta(minutes=10)
                forfeit_time = race.thread_timeout_time

                thread = self.bot.get_channel(race.discord_thread_id)
                if not thread:
                    logger.warning("Cannot access thread for race %s", race.id)
                    continue

                now = datetime.now(timezone.utc)

                # Send warning only if not already sent
                if warning_time <= now < forfeit_time and not getattr(race, "warning_sent", False):
                    await thread.send(
                        f"<@{race.user.discord_id}>, your race will be forfeited on "
                        f"{discord.utils.format_dt(forfeit_time, 'f')} "
                        f"({discord.utils.format_dt(forfeit_time, 'R')}) if you don't start it.",
                        allowed_mentions=discord.AllowedMentions(users=True)
                    )
                    race.warning_sent = True
                    await race.save()

                # Auto-forfeit
                if forfeit_time <= now:
                    await thread.send(
                        f"<@{race.user.discord_id}>, this race has been automatically forfeited due to timeout.",
                        allowed_mentions=discord.AllowedMentions(users=True)
                    )
                    race.status = 'forfeit'
                    await race.save()
                    await self.service.repo.create_audit_log(
                        tournament_id=race.tournament_id,
                        action="auto_forfeit",
                        details=f"Race {race.id} automatically forfeited (pending timeout)",
                        user_id=None,
                    )

        except Exception as e:
            logger.error("Error in timeout_pending_races: %s", e, exc_info=True)

    @tasks.loop(seconds=60)
    async def timeout_in_progress_races(self):
        """Background task to timeout in-progress races."""
        try:
            in_progress = await AsyncTournamentRace.filter(
                status='in_progress',
                discord_thread_id__isnull=False
            ).prefetch_related('user')

            for race in in_progress:
                if not race.start_time:
                    continue

                # 12 hour timeout
                timeout_time = race.start_time + timedelta(hours=12)

                if datetime.now(timezone.utc) >= timeout_time:
                    thread = self.bot.get_channel(race.discord_thread_id)
                    if thread:
                        await thread.send(
                            f"<@{race.user.discord_id}>, this race has exceeded 12 hours and has been forfeited.",
                            allowed_mentions=discord.AllowedMentions(users=True)
                        )

                    race.status = 'forfeit'
                    await race.save()
                    await self.service.repo.create_audit_log(
                        tournament_id=race.tournament_id,
                        action="auto_forfeit",
                        details=f"Race {race.id} automatically forfeited (12 hour timeout)",
                        user_id=None,
                    )

        except Exception as e:
            logger.error("Error in timeout_in_progress_races: %s", e, exc_info=True)

    @tasks.loop(hours=1)
    async def score_calculation(self):
        """Background task to recalculate scores hourly."""
        try:
            active_tournaments = await AsyncTournament.filter(is_active=True)

            for tournament in active_tournaments:
                logger.info("Recalculating scores for tournament %s", tournament.id)
                try:
                    await self.service.calculate_tournament_scores(
                        user=None,  # System task, no user
                        organization_id=tournament.organization_id,
                        tournament_id=tournament.id,
                        system_task=True,  # Bypass authorization for automated task
                    )
                except Exception as e:
                    logger.error("Error calculating scores for tournament %s: %s", tournament.id, e)

        except Exception as e:
            logger.error("Error in score_calculation: %s", e, exc_info=True)

    @timeout_pending_races.before_loop
    async def before_timeout_pending_races(self):
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    @timeout_in_progress_races.before_loop
    async def before_timeout_in_progress_races(self):
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    @score_calculation.before_loop
    async def before_score_calculation(self):
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    """Setup function to add the cog."""
    await bot.add_cog(AsyncTournamentCommands(bot))
    logger.info("AsyncTournamentCommands cog added")
