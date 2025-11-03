"""
Async Tournament Leaderboard View.

Shows tournament leaderboard with player scores.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament
from components.card import Card
from application.services.async_tournament_service import AsyncTournamentService, LeaderboardEntry


class AsyncLeaderboardView:
    """View for async tournament leaderboard."""

    def __init__(self, user: User, tournament: AsyncTournament):
        self.user = user
        self.tournament = tournament
        self.service = AsyncTournamentService()

    async def render(self):
        """Render the leaderboard view."""
        with Card.create(title=f'{self.tournament.name} - Leaderboard'):
            # Tournament info
            with ui.element('div').classes('mb-4'):
                ui.markdown(f"**{self.tournament.description or 'No description'}**")
                ui.label(f'Runs per pool: {self.tournament.runs_per_pool}').classes('text-sm text-secondary')

            # Get leaderboard
            leaderboard = await self.service.get_leaderboard(
                self.user,
                self.tournament.organization_id,
                self.tournament.id
            )

            if not leaderboard:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('leaderboard').classes('text-secondary icon-large')
                    ui.label('No entries yet').classes('text-secondary')
                return

            # Leaderboard table
            await self._render_leaderboard_table(leaderboard)

    async def _render_leaderboard_table(self, leaderboard: list[LeaderboardEntry]):
        """Render leaderboard table."""
        # Fetch pools for column headers
        await self.tournament.fetch_related('pools')
        pools = self.tournament.pools

        with ui.element('div').classes('w-full overflow-x-auto'):
            with ui.element('table').classes('data-table'):
                # Header
                with ui.element('thead'):
                    with ui.element('tr'):
                        ui.element('th').classes('').add_slot('default', 'Rank')
                        ui.element('th').classes('').add_slot('default', 'Player')
                        ui.element('th').classes('').add_slot('default', 'Score')
                        ui.element('th').classes('').add_slot('default', 'Estimate')

                        # Pool columns
                        for pool in pools:
                            for i in range(self.tournament.runs_per_pool):
                                header = f'{pool.name} #{i+1}' if self.tournament.runs_per_pool > 1 else pool.name
                                ui.element('th').classes('').add_slot('default', header)

                        ui.element('th').classes('').add_slot('default', 'Finished')
                        ui.element('th').classes('').add_slot('default', 'Forfeit')
                        ui.element('th').classes('').add_slot('default', 'Unplayed')

                # Body
                with ui.element('tbody'):
                    # Sort by score descending
                    sorted_leaderboard = sorted(leaderboard, key=lambda e: e.score, reverse=True)
                    for rank, entry in enumerate(sorted_leaderboard, 1):
                        await self._render_leaderboard_row(rank, entry, pools)

    async def _render_leaderboard_row(self, rank: int, entry: LeaderboardEntry, pools: list):
        """Render a single leaderboard row."""
        with ui.element('tr'):
            # Rank
            ui.element('td').classes('').add_slot('default', str(rank))

            # Player
            with ui.element('td'):
                # Link to player's race history
                player_link = f'/tournaments/{self.tournament.organization_id}/async/{self.tournament.id}/player/{entry.user.id}'
                ui.link(entry.user.discord_username, player_link)

            # Score
            ui.element('td').classes('font-weight-bold').add_slot('default', f'{entry.score:.3f}')

            # Estimate
            ui.element('td').classes('').add_slot('default', f'{entry.estimate:.3f}')

            # Pool races (in order)
            race_idx = 0
            for _ in pools:
                for _ in range(self.tournament.runs_per_pool):
                    if race_idx < len(entry.races):
                        race = entry.races[race_idx]
                        race_idx += 1
                    else:
                        race = None

                    with ui.element('td'):
                        if race and race.score is not None:
                            # Link to race/permalink details
                            permalink_link = f'/tournaments/{self.tournament.organization_id}/async/{self.tournament.id}/permalink/{race.permalink_id}'
                            ui.link(race.score_formatted, permalink_link)
                        else:
                            ui.label('—')

            # Counts
            ui.element('td').classes('').add_slot('default', str(entry.finished_race_count))
            ui.element('td').classes('').add_slot('default', str(entry.forfeited_race_count))
            ui.element('td').classes('').add_slot('default', str(entry.unattempted_race_count))
