"""
Async Tournament Dashboard View.

Shows a player's own races in an async tournament.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament, AsyncTournamentRace
from components.card import Card
from application.services.async_tournament_service import AsyncTournamentService


class AsyncDashboardView:
    """View for a player's async tournament dashboard."""

    def __init__(self, user: User, tournament: AsyncTournament):
        self.user = user
        self.tournament = tournament
        self.service = AsyncTournamentService()

    async def render(self):
        """Render the dashboard view."""
        with Card.create(title=f'{self.tournament.name} - My Dashboard'):
            # Tournament info
            with ui.element('div').classes('mb-4'):
                ui.markdown(f"**{self.tournament.description or 'No description'}**")
                if self.tournament.is_active:
                    ui.label('Tournament Active').classes('badge badge-success')
                else:
                    ui.label('Tournament Closed').classes('badge badge-danger')

            # Get player's races
            races = await self.service.get_user_races(
                self.user,
                self.tournament.organization_id,
                self.tournament.id
            )

            if not races:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('emoji_events').classes('text-secondary icon-large')
                    ui.label('No races yet').classes('text-secondary')
                    ui.label('Start a race from the Discord channel to begin').classes('text-secondary text-sm')
                return

            # Races table
            await self._render_races_table(races)

    async def _render_races_table(self, races: list[AsyncTournamentRace]):
        """Render table of user's races."""
        with ui.element('div').classes('w-full overflow-x-auto'):
            with ui.element('table').classes('data-table'):
                # Header
                with ui.element('thead'):
                    with ui.element('tr'):
                        ui.element('th').classes('').add_slot('default', 'ID')
                        ui.element('th').classes('').add_slot('default', 'Date/Time')
                        ui.element('th').classes('').add_slot('default', 'Pool')
                        ui.element('th').classes('').add_slot('default', 'Permalink')
                        ui.element('th').classes('').add_slot('default', 'VOD')
                        ui.element('th').classes('').add_slot('default', 'Thread')
                        ui.element('th').classes('').add_slot('default', 'Finish Time')
                        ui.element('th').classes('').add_slot('default', 'Score')
                        ui.element('th').classes('').add_slot('default', 'Status')

                # Body
                with ui.element('tbody'):
                    for race in races:
                        await self._render_race_row(race)

    async def _render_race_row(self, race: AsyncTournamentRace):
        """Render a single race row."""
        # Fetch related data
        await race.fetch_related('permalink', 'permalink__pool')

        with ui.element('tr'):
            # ID
            ui.element('td').classes('').add_slot('default', str(race.id))

            # Date/Time
            if race.thread_open_time:
                time_str = race.thread_open_time.strftime('%Y-%m-%d %H:%M')
            else:
                time_str = 'N/A'
            ui.element('td').classes('').add_slot('default', time_str)

            # Pool
            ui.element('td').classes('').add_slot('default', race.permalink.pool.name)

            # Permalink
            with ui.element('td'):
                ui.link(race.permalink.url, race.permalink.url, new_tab=True)

            # VOD
            with ui.element('td'):
                if race.runner_vod_url:
                    ui.link('VOD', race.runner_vod_url, new_tab=True)
                else:
                    ui.label('—')

            # Thread
            with ui.element('td'):
                if race.discord_thread_id:
                    thread_url = f'https://discord.com/channels/@me/{race.discord_thread_id}'
                    ui.link('Thread', thread_url, new_tab=True)
                else:
                    ui.label('—')

            # Finish Time
            ui.element('td').classes('').add_slot('default', race.elapsed_time_formatted)

            # Score
            ui.element('td').classes('').add_slot('default', race.score_formatted)

            # Status
            with ui.element('td'):
                status_badge_class = {
                    'finished': 'badge-success',
                    'in_progress': 'badge-info',
                    'pending': 'badge-warning',
                    'forfeit': 'badge-danger',
                    'disqualified': 'badge-danger',
                }.get(race.status, 'badge')
                ui.label(race.status_formatted).classes(f'badge {status_badge_class}')
