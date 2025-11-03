"""
Discord UI components for async tournaments.

Provides persistent views and buttons for race management in Discord.
"""

import discord
from discord import ui
import asyncio
import logging
from slugify import slugify

from models import User
from models.async_tournament import AsyncTournament, AsyncTournamentRace
from application.services.async_tournament_service import AsyncTournamentService
from application.repositories.async_tournament_repository import AsyncTournamentRepository

logger = logging.getLogger(__name__)


class AsyncTournamentMainView(ui.View):
    """Main view for async tournament channels with 'Start New Race' button."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Start New Async Run",
        style=discord.ButtonStyle.green,
        emoji="🏁",
        custom_id="async_tournament:new_race"
    )
    async def new_race(self, interaction: discord.Interaction, button: ui.Button):
        """Handle new race button click."""
        # Get tournament for this channel
        repo = AsyncTournamentRepository()
        tournament = await AsyncTournament.get_or_none(discord_channel_id=interaction.channel_id)

        if not tournament:
            await interaction.response.send_message(
                "This channel is not configured for async tournaments.",
                ephemeral=True
            )
            return

        if not tournament.is_active:
            await interaction.response.send_message(
                "This tournament is not currently active.",
                ephemeral=True
            )
            return

        # Get user
        user = await User.get_or_none(discord_id=interaction.user.id)
        if not user:
            await interaction.response.send_message(
                "You must link your account first. Please log in to the web application.",
                ephemeral=True
            )
            return

        # Get service
        service = AsyncTournamentService()

        # Check if user is in the organization
        from application.services.organization_service import OrganizationService
        org_service = OrganizationService()
        is_member = await org_service.is_member(user, tournament.organization_id)

        if not is_member:
            await interaction.response.send_message(
                "You must be a member of this tournament's organization to participate.",
                ephemeral=True
            )
            return

        # Get user's race history
        user_races = await service.get_user_races(user, tournament.organization_id, tournament.id)

        # Get pools
        await tournament.fetch_related('pools')
        pools = list(tournament.pools)

        if not pools:
            await interaction.response.send_message(
                "This tournament has no pools configured yet.",
                ephemeral=True
            )
            return

        # Check how many races completed from each pool
        pool_counts = {}
        for pool in pools:
            count = len([
                r for r in user_races
                if not r.reattempted and r.permalink.pool_id == pool.id
            ])
            pool_counts[pool.id] = count

        # Find pools with available slots
        available_pools = [
            pool for pool in pools
            if pool_counts.get(pool.id, 0) < tournament.runs_per_pool
        ]

        if not available_pools:
            await interaction.response.send_message(
                "You have completed all available pools for this tournament.",
                ephemeral=True
            )
            return

        # Show pool selection
        view = PoolSelectionView(available_pools, tournament, user)
        await interaction.response.send_message(
            "You must start your race within 10 minutes of clicking 'Confirm'.\n"
            "Failure to do so will result in a forfeit.\n\n"
            "**Please be absolutely certain you're ready to begin.**\n\n"
            "Select a pool to race:",
            view=view,
            ephemeral=True
        )


class PoolSelectionView(ui.View):
    """View for selecting which pool to race."""

    def __init__(self, pools, tournament: AsyncTournament, user: User):
        super().__init__(timeout=60)
        self.pools = pools
        self.tournament = tournament
        self.user = user
        self.selected_pool = None

        # Add pool select menu
        options = [
            discord.SelectOption(label=pool.name, value=str(pool.id))
            for pool in pools
        ]
        select = ui.Select(
            placeholder="Select a pool",
            options=options,
            custom_id="pool_select"
        )
        select.callback = self.pool_selected
        self.add_item(select)

    async def pool_selected(self, interaction: discord.Interaction):
        """Handle pool selection."""
        pool_id = int(interaction.data['values'][0])
        self.selected_pool = next(p for p in self.pools if p.id == pool_id)

        # Enable confirm button
        for item in self.children:
            if isinstance(item, ui.Button) and item.custom_id == "confirm_race":
                item.disabled = False

        await interaction.response.edit_message(
            content=f"Selected pool: **{self.selected_pool.name}**\n\n"
                    f"Click 'Confirm' to create your race thread.",
            view=self
        )

    @ui.button(
        label="Confirm - Point of No Return!",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="confirm_race",
        disabled=True,
        row=1
    )
    async def confirm_race(self, interaction: discord.Interaction, button: ui.Button):
        """Confirm race creation."""
        if not self.selected_pool:
            await interaction.response.send_message("Please select a pool first.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Check for existing active races
        service = AsyncTournamentService()
        existing_races = await service.get_active_races_for_user(
            user=self.user,
            organization_id=self.tournament.organization_id,
            tournament_id=self.tournament.id
        )

        if existing_races:
            await interaction.followup.send(
                "You already have an active race. Please complete or forfeit it first.",
                ephemeral=True
            )
            return

        # Get a random eligible permalink from the selected pool
        import random
        from application.services.async_tournament_service import MAX_POOL_IMBALANCE

        await self.selected_pool.fetch_related('permalinks')
        all_permalinks = list(self.selected_pool.permalinks)

        # Get user's race history for this pool
        user_pool_races = await AsyncTournamentRace.filter(
            user_id=self.user.id,
            tournament_id=self.tournament.id,
            permalink__pool_id=self.selected_pool.id,
            reattempted=False
        ).prefetch_related('permalink')

        played_permalinks = {r.permalink_id for r in user_pool_races}
        eligible_permalinks = [p for p in all_permalinks if p.id not in played_permalinks]

        if not eligible_permalinks:
            await interaction.followup.send(
                "No eligible permalinks available in this pool.",
                ephemeral=True
            )
            return

        # Pick a random permalink
        permalink = random.choice(eligible_permalinks)

        # Create private thread
        thread = await interaction.channel.create_thread(
            name=f"{slugify(interaction.user.name, lowercase=False, max_length=20)} - {self.selected_pool.name}",
            type=discord.ChannelType.private_thread
        )

        # Create race record
        race = await service.create_race(
            user=self.user,
            organization_id=self.tournament.organization_id,
            tournament_id=self.tournament.id,
            permalink_id=permalink.id,
            discord_thread_id=thread.id,
        )

        if not race:
            await interaction.followup.send("Failed to create race.", ephemeral=True)
            return

        # Invite user to thread
        await thread.add_user(interaction.user)

        # Post race info in thread
        embed = discord.Embed(title="Tournament Async Run", color=discord.Color.blue())
        embed.add_field(name="Pool", value=self.selected_pool.name, inline=False)
        embed.add_field(name="Permalink", value=permalink.url, inline=False)
        if permalink.notes:
            embed.add_field(name="Notes", value=permalink.notes, inline=False)
        embed.set_footer(text=f"Race ID: {race.id}")

        message = """⚠️ **Please read these reminders before clicking Ready!** ⚠️

1. You should record your run for verification purposes.
2. If you have any technical issues with Discord or this bot, **do not forfeit**. Continue your run and contact an admin after.
3. If you forfeit, you will receive a score of zero for this race.

Good luck and have fun!"""

        await thread.send(content=message, embed=embed, view=RaceReadyView())

        await interaction.followup.send(
            f"Successfully created {thread.mention}. Please join that thread for more details.",
            ephemeral=True
        )

    @ui.button(
        label="Cancel",
        style=discord.ButtonStyle.red,
        emoji="❌",
        custom_id="cancel_race",
        row=1
    )
    async def cancel_race(self, interaction: discord.Interaction, button: ui.Button):
        """Cancel race creation."""
        await interaction.response.edit_message(
            content="Race creation cancelled.",
            view=None
        )


class RaceReadyView(ui.View):
    """View for the race ready state (before countdown)."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Ready (start countdown)",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="async_race:ready"
    )
    async def ready(self, interaction: discord.Interaction, button: ui.Button):
        """Start the race countdown."""
        # Get race for this thread
        race = await AsyncTournamentRace.get_or_none(discord_thread_id=interaction.channel.id).prefetch_related('user')

        if not race:
            await interaction.response.send_message(
                "This thread is not a valid race thread.",
                ephemeral=True
            )
            return

        if race.user.discord_id != interaction.user.id:
            await interaction.response.send_message(
                "Only the race participant can start this race.",
                ephemeral=True
            )
            return

        if race.status != 'pending':
            await interaction.response.send_message(
                "This race must be in pending state to start.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self)

        # Start countdown
        service = AsyncTournamentService()
        await service.repo.create_audit_log(
            tournament_id=race.tournament_id,
            action="race_countdown",
            details=f"Race {race.id} starting countdown",
            user_id=race.user_id,
        )

        for i in range(10, 0, -1):
            await interaction.channel.send(f"{i}...")
            await asyncio.sleep(1)

        # Mark race as started
        race = await service.start_race(
            user=race.user,
            organization_id=race.tournament.organization_id,
            race_id=race.id,
        )

        await interaction.channel.send("**GO!**", view=RaceInProgressView())

    @ui.button(
        label="Forfeit",
        style=discord.ButtonStyle.red,
        emoji="🏳️",
        custom_id="async_race:forfeit_ready"
    )
    async def forfeit(self, interaction: discord.Interaction, button: ui.Button):
        """Forfeit the race."""
        await self._handle_forfeit(interaction)

    async def _handle_forfeit(self, interaction: discord.Interaction):
        """Common forfeit logic."""
        race = await AsyncTournamentRace.get_or_none(discord_thread_id=interaction.channel.id).prefetch_related('user')

        if not race:
            await interaction.response.send_message("Invalid race thread.", ephemeral=True)
            return

        if race.user.discord_id != interaction.user.id:
            await interaction.response.send_message("Only the race participant can forfeit.", ephemeral=True)
            return

        await interaction.response.send_message(
            "Are you sure you wish to forfeit? This action **cannot be undone**. "
            "This race will be scored as **zero**.",
            view=ForfeitConfirmView(),
            ephemeral=True
        )


class RaceInProgressView(ui.View):
    """View for race in progress."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Finish",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="async_race:finish"
    )
    async def finish(self, interaction: discord.Interaction, button: ui.Button):
        """Finish the race."""
        race = await AsyncTournamentRace.get_or_none(discord_thread_id=interaction.channel.id).prefetch_related('user', 'tournament')

        if not race:
            await interaction.response.send_message("Invalid race thread.", ephemeral=True)
            return

        if race.user.discord_id != interaction.user.id:
            await interaction.response.send_message("Only the race participant can finish.", ephemeral=True)
            return

        if race.status != 'in_progress':
            await interaction.response.send_message("Race must be in progress to finish.", ephemeral=True)
            return

        await interaction.response.defer()

        # Finish the race
        service = AsyncTournamentService()
        race = await service.finish_race(
            user=race.user,
            organization_id=race.tournament.organization_id,
            race_id=race.id,
        )

        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.followup.edit_message(message_id=interaction.message.id, view=self)

        await interaction.followup.send(
            f"Your finish time of **{race.elapsed_time_formatted}** has been recorded. Thank you for playing!\n\n"
            f"You may submit additional information (VOD, notes) via the web interface."
        )

    @ui.button(
        label="Forfeit",
        style=discord.ButtonStyle.red,
        emoji="🏳️",
        custom_id="async_race:forfeit_progress"
    )
    async def forfeit(self, interaction: discord.Interaction, button: ui.Button):
        """Forfeit the race."""
        await RaceReadyView()._handle_forfeit(interaction)

    @ui.button(
        label="Get Timer",
        style=discord.ButtonStyle.gray,
        emoji="⏱️",
        custom_id="async_race:timer"
    )
    async def get_timer(self, interaction: discord.Interaction, button: ui.Button):
        """Get current elapsed time."""
        race = await AsyncTournamentRace.get_or_none(discord_thread_id=interaction.channel.id)

        if not race or not race.start_time:
            await interaction.response.send_message("Timer not available.", ephemeral=True)
            return

        # Calculate elapsed time for in-progress races
        if race.status == 'in_progress':
            elapsed = datetime.utcnow() - race.start_time
        else:
            elapsed = race.elapsed_time

        if not elapsed:
            await interaction.response.send_message("Timer not available.", ephemeral=True)
            return

        # Format elapsed time as H:MM:SS
        def format_timedelta(td: timedelta) -> str:
            total_seconds = int(td.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}:{minutes:02}:{seconds:02}"

        formatted = format_timedelta(elapsed)

        await interaction.response.send_message(
            f"Timer: **{formatted}**",
            ephemeral=True
        )


class ForfeitConfirmView(ui.View):
    """Confirmation view for forfeiting a race."""

    def __init__(self):
        super().__init__(timeout=60)

    @ui.button(
        label="Confirm Forfeit",
        style=discord.ButtonStyle.red,
        emoji="🏳️"
    )
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        """Confirm forfeit."""
        race = await AsyncTournamentRace.get_or_none(discord_thread_id=interaction.channel.id).prefetch_related('user', 'tournament')

        if not race:
            await interaction.response.send_message("Invalid race thread.", ephemeral=True)
            return

        if race.user.discord_id != interaction.user.id:
            await interaction.response.send_message("Only the race participant can forfeit.", ephemeral=True)
            return

        # Forfeit the race
        service = AsyncTournamentService()
        await service.forfeit_race(
            user=race.user,
            organization_id=race.tournament.organization_id,
            race_id=race.id,
        )

        await interaction.response.send_message(
            f"This run has been forfeited by {interaction.user.mention}."
        )

        # Disable all buttons in parent message
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
