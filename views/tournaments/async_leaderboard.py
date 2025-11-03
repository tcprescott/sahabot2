"""
Async Tournament Leaderboard View.

Shows tournament leaderboard with player scores and filtering options.
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
        # Check if results should be hidden
        if self.tournament.hide_results and self.tournament.is_active:
            await self._render_hidden_state()
            return
        
        # Get leaderboard
        leaderboard = await self.service.get_leaderboard(
            self.user,
            self.tournament.organization_id,
            self.tournament.id
        )

        # Get pools
        await self.tournament.fetch_related('pools')
        pools = list(self.tournament.pools)

        # Render header
        await self._render_header(leaderboard)

        # Render leaderboard
        if not leaderboard:
            await self._render_empty_state()
        else:
            await self._render_leaderboard_table(leaderboard, pools)

    async def _render_hidden_state(self):
        """Render hidden state when results are private."""
        with Card.create(title=f'{self.tournament.name} - Leaderboard'):
            with ui.element('div').classes('flex flex-wrap justify-between items-center gap-md'):
                # Description
                if self.tournament.description:
                    with ui.element('div').classes('flex-grow'):
                        ui.markdown(self.tournament.description)
        
        with Card.create(title='Standings'):
            with ui.element('div').classes('text-center py-8'):
                ui.icon('visibility_off').classes('text-secondary icon-large')
                ui.label('Results Hidden').classes('text-secondary text-lg mt-4')
                ui.label('Player results will be visible after the tournament ends').classes('text-secondary mt-2')

    async def _render_header(self, leaderboard: list[LeaderboardEntry]):
        """Render tournament header with stats."""
        with Card.create(title=f'{self.tournament.name} - Leaderboard'):
            with ui.element('div').classes('flex flex-wrap justify-between items-center gap-md'):
                # Description
                if self.tournament.description:
                    with ui.element('div').classes('flex-grow'):
                        ui.markdown(self.tournament.description)

                # Stats
                with ui.element('div').classes('flex gap-md'):
                    # Participant count
                    with ui.element('div').classes('text-center'):
                        ui.label(str(len(leaderboard))).classes('stat-value text-lg')
                        ui.label('Participants').classes('stat-label text-xs')

                    # Runs per pool
                    with ui.element('div').classes('text-center'):
                        ui.label(str(self.tournament.runs_per_pool)).classes('stat-value text-lg')
                        ui.label('Runs/Pool').classes('stat-label text-xs')

    async def _render_empty_state(self):
        """Render empty state."""
        with Card.create(title='Standings'):
            with ui.element('div').classes('text-center py-8'):
                ui.icon('leaderboard').classes('text-secondary icon-large')
                ui.label('No entries yet').classes('text-secondary text-lg mt-4')
                ui.label('Be the first to complete a race!').classes('text-secondary mt-2')

    async def _render_leaderboard_table(self, leaderboard: list[LeaderboardEntry], pools: list):
        """Render leaderboard table with filtering."""
        # Sort by score descending
        sorted_leaderboard = sorted(leaderboard, key=lambda e: e.score, reverse=True)

        with Card.create(title='Standings'):
            # Filter controls
            with ui.element('div').classes('flex flex-wrap gap-md mb-4'):
                # Search by player name
                search_input = ui.input(
                    label='Search Player',
                    placeholder='Enter player name...'
                ).classes('filter-select')

                # Min races filter
                min_races_input = ui.number(
                    label='Min Completed Races',
                    value=0,
                    min=0
                ).classes('filter-select')

            # Container for filtered results
            leaderboard_container = ui.element('div')

            async def refresh_leaderboard():
                """Refresh leaderboard based on filters."""
                leaderboard_container.clear()
                with leaderboard_container:
                    await self._render_filtered_leaderboard(
                        sorted_leaderboard,
                        pools,
                        search_input.value or '',
                        int(min_races_input.value or 0)
                    )

            search_input.on('update:model-value', refresh_leaderboard)
            min_races_input.on('update:model-value', refresh_leaderboard)

            # Initial render
            with leaderboard_container:
                await self._render_filtered_leaderboard(sorted_leaderboard, pools, '', 0)

    async def _render_filtered_leaderboard(
        self,
        leaderboard: list[LeaderboardEntry],
        pools: list,
        search_term: str,
        min_races: int
    ):
        """Render filtered leaderboard content."""
        # Apply filters
        filtered = leaderboard
        if search_term:
            filtered = [
                e for e in filtered
                if search_term.lower() in e.user.get_display_name().lower()
            ]
        if min_races > 0:
            filtered = [e for e in filtered if e.finished_race_count >= min_races]

        if not filtered:
            with ui.element('div').classes('text-center py-4'):
                ui.label('No players match the selected filters').classes('text-secondary')
            return

        # Desktop: Full table
        with ui.element('div').classes('hidden md:block'):
            await self._render_desktop_leaderboard(filtered, pools)

        # Mobile: Card view
        with ui.element('div').classes('block md:hidden'):
            await self._render_mobile_leaderboard(filtered)

    async def _render_desktop_leaderboard(self, leaderboard: list[LeaderboardEntry], pools):  # noqa: ARG002
        """Render desktop leaderboard table."""
        with ui.element('div').classes('w-full overflow-x-auto'):
            with ui.element('table').classes('data-table'):
                # Header
                with ui.element('thead'):
                    with ui.element('tr'):
                        ui.element('th').add_slot('default', 'Rank')
                        ui.element('th').add_slot('default', 'Player')
                        ui.element('th').add_slot('default', 'Total Score')
                        ui.element('th').add_slot('default', 'Completed')
                        ui.element('th').add_slot('default', 'Forfeit')
                        ui.element('th').add_slot('default', 'Remaining')
                        ui.element('th').add_slot('default', 'Actions')

                # Body
                with ui.element('tbody'):
                    for rank, entry in enumerate(leaderboard, 1):
                        await self._render_desktop_row(rank, entry)

    async def _render_desktop_row(self, rank: int, entry: LeaderboardEntry):
        """Render desktop leaderboard row."""
        # Highlight current user
        row_class = 'bg-primary-subtle' if entry.user.id == self.user.id else ''

        with ui.element('tr').classes(row_class):
            # Rank with medal emoji for top 3
            rank_display = str(rank)
            if rank == 1:
                rank_display = '🥇 1st'
            elif rank == 2:
                rank_display = '🥈 2nd'
            elif rank == 3:
                rank_display = '🥉 3rd'
            ui.element('td').add_slot('default', rank_display)

            # Player
            with ui.element('td'):
                player_name = entry.user.get_display_name()
                if entry.user.id == self.user.id:
                    player_name += ' (You)'
                ui.label(player_name).classes('font-bold')

            # Total Score
            ui.element('td').classes('font-bold text-success').add_slot('default', f'{entry.score:.1f}')

            # Completed
            ui.element('td').add_slot('default', str(entry.finished_race_count))

            # Forfeit
            forfeit_class = 'text-danger' if entry.forfeited_race_count > 0 else ''
            ui.element('td').classes(forfeit_class).add_slot('default', str(entry.forfeited_race_count))

            # Remaining
            ui.element('td').add_slot('default', str(entry.unattempted_race_count))

            # Actions
            with ui.element('td'):
                player_link = f'/org/{self.tournament.organization_id}/async/{self.tournament.id}/player/{entry.user.id}'
                ui.link('View History', player_link).classes('btn-link')

    async def _render_mobile_leaderboard(self, leaderboard: list[LeaderboardEntry]):
        """Render mobile leaderboard cards."""
        for rank, entry in enumerate(leaderboard, 1):
            await self._render_mobile_card(rank, entry)

    async def _render_mobile_card(self, rank: int, entry: LeaderboardEntry):
        """Render mobile leaderboard card."""
        # Highlight current user
        card_class = 'border-primary' if entry.user.id == self.user.id else ''

        with ui.element('div').classes(f'card mb-4 {card_class}'):
            with ui.element('div').classes('card-body'):
                # Rank and Player
                with ui.element('div').classes('flex justify-between items-center mb-3'):
                    with ui.element('div'):
                        # Rank with medal
                        rank_display = str(rank)
                        if rank == 1:
                            rank_display = '🥇 1st'
                        elif rank == 2:
                            rank_display = '🥈 2nd'
                        elif rank == 3:
                            rank_display = '🥉 3rd'
                        ui.label(rank_display).classes('badge badge-primary')

                    with ui.element('div'):
                        player_name = entry.user.get_display_name()
                        if entry.user.id == self.user.id:
                            player_name += ' (You)'
                        ui.label(player_name).classes('font-bold')

                # Score (large)
                with ui.element('div').classes('text-center my-3'):
                    ui.label(f'{entry.score:.1f}').classes('text-3xl font-bold text-success')
                    ui.label('Total Score').classes('text-sm text-secondary')

                # Stats grid
                with ui.element('div').classes('grid grid-cols-3 gap-md mt-3'):
                    # Completed
                    with ui.element('div').classes('text-center'):
                        ui.label(str(entry.finished_race_count)).classes('font-bold')
                        ui.label('Completed').classes('text-xs text-secondary')

                    # Forfeit
                    with ui.element('div').classes('text-center'):
                        forfeit_class = 'text-danger' if entry.forfeited_race_count > 0 else ''
                        ui.label(str(entry.forfeited_race_count)).classes(f'font-bold {forfeit_class}')
                        ui.label('Forfeit').classes('text-xs text-secondary')

                    # Remaining
                    with ui.element('div').classes('text-center'):
                        ui.label(str(entry.unattempted_race_count)).classes('font-bold')
                        ui.label('Remaining').classes('text-xs text-secondary')

                # View history button
                player_link = f'/org/{self.tournament.organization_id}/async/{self.tournament.id}/player/{entry.user.id}'
                ui.button(
                    'View Race History',
                    on_click=lambda: ui.navigate.to(player_link)
                ).classes('btn btn-sm w-full mt-3')

