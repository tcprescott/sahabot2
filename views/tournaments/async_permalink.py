"""
Async Tournament Permalink View.

Shows all races for a specific permalink/seed.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament
from components.card import Card
from application.services.async_tournament_service import AsyncTournamentService


class AsyncPermalinkView:
    """View for races on a specific permalink."""

    def __init__(self, user: User, tournament: AsyncTournament, permalink_id: int):
        self.user = user
        self.tournament = tournament
        self.permalink_id = permalink_id
        self.service = AsyncTournamentService()

    async def render(self):
        """Render the permalink view."""
        # Get permalink
        permalink = await self.service.get_permalink(
            self.user,
            self.tournament.organization_id,
            self.tournament.id,
            self.permalink_id
        )

        if not permalink:
            ui.label('Permalink not found').classes('text-danger')
            return

        await permalink.fetch_related('pool')

        with Card.create(title=f'{permalink.pool.name} - {permalink.url}'):
            # Permalink info
            with ui.element('div').classes('mb-4'):
                with ui.row().classes('gap-4'):
                    ui.label(f'Pool: {permalink.pool.name}').classes('font-weight-bold')
                    if permalink.par_time is not None:
                        # Hide par time if results are hidden and tournament is active
                        if not (self.tournament.hide_results and self.tournament.is_active):
                            ui.label(f'Par Time: {permalink.par_time_formatted}').classes('badge badge-info')
                        else:
                            ui.label('Par Time: Hidden').classes('badge badge-info')

                ui.link(permalink.url, permalink.url, new_tab=True)

                if permalink.notes:
                    with ui.element('div').classes('mt-2'):
                        ui.label('Notes:').classes('font-weight-bold')
                        ui.markdown(permalink.notes)

            # Check if results should be hidden
            if self.tournament.hide_results and self.tournament.is_active:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('visibility_off').classes('text-secondary icon-large')
                    ui.label('Race Results Hidden').classes('text-secondary text-lg mt-4')
                    ui.label('Race results will be visible after the tournament ends').classes('text-secondary mt-2')
                return

            # Get races for this permalink
            races = await self.service.get_permalink_races(
                self.user,
                self.tournament.organization_id,
                self.tournament.id,
                self.permalink_id
            )

            if not races:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('emoji_events').classes('text-secondary icon-large')
                    ui.label('No races on this permalink yet').classes('text-secondary')
                return

            # Races table
            await self._render_races_table(races)

    async def _render_races_table(self, races):
        """Render table of races."""
        with ui.element('div').classes('w-full overflow-x-auto'):
            with ui.element('table').classes('data-table'):
                # Header
                with ui.element('thead'):
                    with ui.element('tr'):
                        ui.element('th').classes('').add_slot('default', 'ID')
                        ui.element('th').classes('').add_slot('default', 'Player')
                        ui.element('th').classes('').add_slot('default', 'VOD')
                        ui.element('th').classes('').add_slot('default', 'Thread')
                        ui.element('th').classes('').add_slot('default', 'Finish Time')
                        ui.element('th').classes('').add_slot('default', 'Score')
                        ui.element('th').classes('').add_slot('default', 'Status')

                # Body
                with ui.element('tbody'):
                    # Sort by score descending
                    sorted_races = sorted(
                        [r for r in races if r.status == 'finished' and r.score is not None],
                        key=lambda r: r.score,
                        reverse=True
                    )
                    for race in sorted_races:
                        await self._render_race_row(race)

    async def _render_race_row(self, race):
        """Render a single race row."""
        # Fetch related data
        await race.fetch_related('user')

        with ui.element('tr'):
            # ID
            ui.element('td').classes('').add_slot('default', str(race.id))

            # Player
            with ui.element('td'):
                player_link = f'/org/{self.tournament.organization_id}/async/{self.tournament.id}/player/{race.user.id}'
                ui.link(race.user.discord_username, player_link)

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
            ui.element('td').classes('font-weight-bold').add_slot('default', race.score_formatted)

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
