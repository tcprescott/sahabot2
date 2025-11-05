"""
Async Tournament Dashboard View.

Shows a player's own races in an async tournament with stats and progress.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament, AsyncTournamentRace
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from application.services.async_tournament_service import AsyncTournamentService


class AsyncDashboardView:
    """View for a player's async tournament dashboard."""

    def __init__(self, user: User, tournament: AsyncTournament):
        self.user = user
        self.tournament = tournament
        self.service = AsyncTournamentService()

    async def render(self):
        """Render the dashboard view."""
        # Get player's races
        races = await self.service.get_user_races(
            self.user,
            self.tournament.organization_id,
            self.tournament.id
        )

        # Get pools
        await self.tournament.fetch_related('pools')
        pools = list(self.tournament.pools)

        # Render tournament header
        await self._render_tournament_header()

        # Render player stats
        await self._render_player_stats(races, pools)

        # Render pool progress
        await self._render_pool_progress(races, pools)

        # Render races table
        if races:
            await self._render_races_table(races)
        else:
            await self._render_no_races_message()

    async def _render_tournament_header(self):
        """Render tournament header with info and status."""
        with Card.create(title=self.tournament.name):
            with ui.element('div').classes('flex flex-wrap gap-md items-center'):
                # Description
                if self.tournament.description:
                    with ui.element('div').classes('flex-grow'):
                        ui.markdown(self.tournament.description)

                # Status badge
                if self.tournament.is_active:
                    ui.label('🏁 Active').classes('badge badge-success')
                else:
                    ui.label('🏁 Closed').classes('badge badge-danger')

            # Discord channel link
            if self.tournament.discord_channel_id:
                with ui.element('div').classes('mt-2'):
                    ui.icon('discord').classes('inline-block mr-1')
                    discord_url = f'https://discord.com/channels/@me/{self.tournament.discord_channel_id}'
                    ui.link('Go to Tournament Discord Channel', discord_url, new_tab=True).classes('btn-link')

    async def _render_player_stats(self, races: list[AsyncTournamentRace], pools):  # noqa: ARG002
        """Render player statistics card."""
        # Calculate stats
        completed_races = [r for r in races if r.status == 'finished' and not r.reattempted]
        forfeited_races = [r for r in races if r.status == 'forfeit']
        active_races = [r for r in races if r.status in ('pending', 'in_progress')]
        reattempted = any(r.reattempted for r in races)

        # Total score
        total_score = sum(r.score or 0 for r in completed_races)

        # Best race
        best_race = min(completed_races, key=lambda r: r.elapsed_time.total_seconds()) if completed_races else None

        with Card.create(title='My Statistics'):
            with ui.element('div').classes('grid grid-cols-2 md:grid-cols-4 gap-md'):
                # Completed
                with ui.element('div').classes('stat-card'):
                    ui.label(str(len(completed_races))).classes('stat-value')
                    ui.label('Completed').classes('stat-label')

                # Forfeited
                with ui.element('div').classes('stat-card'):
                    ui.label(str(len(forfeited_races))).classes('stat-value text-danger')
                    ui.label('Forfeited').classes('stat-label')

                # Active
                with ui.element('div').classes('stat-card'):
                    ui.label(str(len(active_races))).classes('stat-value text-info')
                    ui.label('Active').classes('stat-label')

                # Total Score
                with ui.element('div').classes('stat-card'):
                    ui.label(f'{total_score:.1f}').classes('stat-value text-success')
                    ui.label('Total Score').classes('stat-label')

            # Best time
            if best_race:
                with ui.element('div').classes('mt-4'):
                    ui.label('🏆 Personal Best: ').classes('font-bold inline-block')
                    ui.label(f'{best_race.elapsed_time_formatted}').classes('inline-block text-success')
                    await best_race.fetch_related('permalink', 'permalink__pool')
                    ui.label(f' on {best_race.permalink.pool.name}').classes('inline-block text-sm')

            # Reattempt status
            if reattempted:
                with ui.element('div').classes('mt-2'):
                    ui.icon('refresh').classes('inline-block text-warning mr-1')
                    ui.label('You have used your reattempt').classes('text-warning inline-block')

    async def _render_pool_progress(self, races: list[AsyncTournamentRace], pools: list):
        """Render pool completion progress."""
        if not pools:
            return

        with Card.create(title='Pool Progress'):
            # Calculate pool completion
            pool_stats = {}
            for pool in pools:
                completed = len([
                    r for r in races
                    if not r.reattempted and r.status == 'finished'
                    and r.permalink.pool_id == pool.id
                ])
                total = self.tournament.runs_per_pool
                pool_stats[pool.id] = {
                    'pool': pool,
                    'completed': completed,
                    'total': total,
                    'remaining': total - completed
                }

            # Render progress bars
            with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 gap-md'):
                for stats in pool_stats.values():
                    pool = stats['pool']
                    completed = stats['completed']
                    total = stats['total']
                    percent = (completed / total * 100) if total > 0 else 0

                    with ui.element('div').classes('pool-progress-card'):
                        # Pool name and counts
                        with ui.element('div').classes('flex justify-between items-center mb-2'):
                            ui.label(pool.name).classes('font-bold')
                            ui.label(f'{completed}/{total}').classes('text-sm')

                        # Progress bar
                        with ui.element('div').classes('progress-bar-container'):
                            with ui.element('div').classes('progress-bar').style(f'width: {percent}%'):
                                pass

                        # Status
                        if stats['remaining'] == 0:
                            ui.label('✓ Complete').classes('text-success text-sm mt-1')
                        else:
                            ui.label(f'{stats["remaining"]} remaining').classes('text-sm mt-1')

    async def _render_no_races_message(self):
        """Render empty state message."""
        with Card.create(title='My Races'):
            with ui.element('div').classes('text-center py-8'):
                ui.icon('emoji_events').classes('text-secondary icon-large')
                ui.label('No races yet').classes('text-secondary text-lg mt-4')
                ui.label('Start a race from the Discord channel to begin your tournament journey!').classes('text-secondary mt-2')

                if self.tournament.discord_channel_id:
                    discord_url = f'https://discord.com/channels/@me/{self.tournament.discord_channel_id}'
                    ui.button(
                        'Go to Discord Channel',
                        on_click=lambda: ui.navigate.to(discord_url, new_tab=True)
                    ).classes('btn btn-primary mt-4')

    async def _render_races_table(self, races: list[AsyncTournamentRace]):
        """Render table of user's races."""

    async def _render_races_table(self, races: list[AsyncTournamentRace]):
        """Render table of user's races."""
        with Card.create(title='My Races'):
            # Filter controls
            with ui.element('div').classes('flex flex-wrap gap-md mb-4'):
                # Status filter
                status_options = ['All', 'Finished', 'In Progress', 'Pending', 'Forfeit']
                status_filter = ui.select(
                    status_options,
                    value='All',
                    label='Status Filter'
                ).classes('filter-select')

                # Sort controls
                sort_options = ['Newest First', 'Oldest First', 'Best Score', 'Worst Score']
                sort_select = ui.select(
                    sort_options,
                    value='Newest First',
                    label='Sort By'
                ).classes('filter-select')

            # Races container (will be refreshed on filter change)
            races_container = ui.element('div')

            async def refresh_races():
                """Refresh races table based on filters."""
                races_container.clear()
                with races_container:
                    await self._render_races_content(
                        races,
                        status_filter.value,
                        sort_select.value
                    )

            status_filter.on('update:model-value', refresh_races)
            sort_select.on('update:model-value', refresh_races)

            # Initial render
            with races_container:
                await self._render_races_content(races, 'All', 'Newest First')

    async def _render_races_content(self, races: list[AsyncTournamentRace], status_filter: str, sort_by: str):
        """Render filtered and sorted races content."""
        # Filter races
        filtered_races = races
        if status_filter != 'All':
            status_map = {
                'Finished': 'finished',
                'In Progress': 'in_progress',
                'Pending': 'pending',
                'Forfeit': 'forfeit'
            }
            filtered_races = [r for r in races if r.status == status_map[status_filter]]

        # Sort races
        if sort_by == 'Newest First':
            filtered_races = sorted(filtered_races, key=lambda r: r.created_at, reverse=True)
        elif sort_by == 'Oldest First':
            filtered_races = sorted(filtered_races, key=lambda r: r.created_at)
        elif sort_by == 'Best Score':
            filtered_races = sorted(
                [r for r in filtered_races if r.score is not None],
                key=lambda r: r.score,
                reverse=True
            )
        elif sort_by == 'Worst Score':
            filtered_races = sorted(
                [r for r in filtered_races if r.score is not None],
                key=lambda r: r.score
            )

        if not filtered_races:
            with ui.element('div').classes('text-center py-4'):
                ui.label('No races match the selected filters').classes('text-secondary')
            return

        # Fetch related data for all races
        for race in filtered_races:
            await race.fetch_related('permalink', 'permalink__pool')

        # Define columns for desktop table
        columns = [
            TableColumn(label='Date', cell_render=self._render_date),
            TableColumn(label='Pool', cell_render=lambda r: ui.label(r.permalink.pool.name)),
            TableColumn(label='Status', cell_render=self._render_status),
            TableColumn(label='Time', key='elapsed_time_formatted'),
            TableColumn(label='Score', cell_render=self._render_score),
            TableColumn(label='VOD', cell_render=self._render_vod),
            TableColumn(label='Actions', cell_render=self._render_actions),
        ]

        # Desktop: Table view
        with ui.element('div').classes('hidden md:block'):
            table = ResponsiveTable(columns=columns, rows=filtered_races)
            await table.render()

        # Mobile: Card view
        with ui.element('div').classes('block md:hidden'):
            for race in filtered_races:
                await self._render_race_card_mobile(race)

    def _render_date(self, race: AsyncTournamentRace):
        """Render date cell."""
        if race.thread_open_time:
            date_str = race.thread_open_time.strftime('%Y-%m-%d %H:%M')
        else:
            date_str = race.created_at.strftime('%Y-%m-%d %H:%M')
        ui.label(date_str)

    def _render_status(self, race: AsyncTournamentRace):
        """Render status cell."""
        status_badge_class = {
            'finished': 'badge-success',
            'in_progress': 'badge-info',
            'pending': 'badge-warning',
            'forfeit': 'badge-danger',
            'disqualified': 'badge-danger',
        }.get(race.status, 'badge')
        status_label = race.status.replace('_', ' ').title()
        if race.reattempted:
            status_label += ' (Reattempt)'
        ui.label(status_label).classes(f'badge {status_badge_class}')

    def _render_score(self, race: AsyncTournamentRace):
        """Render score cell."""
        score_text = f'{race.score:.1f}' if race.score is not None else '—'
        ui.label(score_text)

    def _render_vod(self, race: AsyncTournamentRace):
        """Render VOD cell."""
        if race.runner_vod_url:
            ui.link('Watch', race.runner_vod_url, new_tab=True).classes('btn-link')
        else:
            ui.label('—')

    def _render_actions(self, race: AsyncTournamentRace):
        """Render actions cell."""
        with ui.row().classes('gap-sm'):
            # View permalink
            ui.link(
                'View Seed',
                race.permalink.url,
                new_tab=True
            ).classes('btn-link')  # External link

            # Discord thread
            if race.discord_thread_id:
                thread_url = f'https://discord.com/channels/@me/{race.discord_thread_id}'
                ui.link('Thread', thread_url, new_tab=True).classes('btn-link')

    async def _render_race_card_mobile(self, race: AsyncTournamentRace):
        """Render a single race card for mobile view."""
        await race.fetch_related('permalink', 'permalink__pool')

        with ui.element('div').classes('card mb-4'):
            with ui.element('div').classes('card-body'):
                # Header: Pool and Status
                with ui.element('div').classes('flex justify-between items-center mb-2'):
                    ui.label(race.permalink.pool.name).classes('font-bold')
                    status_badge_class = {
                        'finished': 'badge-success',
                        'in_progress': 'badge-info',
                        'pending': 'badge-warning',
                        'forfeit': 'badge-danger',
                        'disqualified': 'badge-danger',
                    }.get(race.status, 'badge')
                    status_label = race.status.replace('_', ' ').title()
                    if race.reattempted:
                        status_label += ' (Reattempt)'
                    ui.label(status_label).classes(f'badge {status_badge_class}')

                # Date
                if race.thread_open_time:
                    date_str = race.thread_open_time.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = race.created_at.strftime('%Y-%m-%d %H:%M')
                with ui.element('div').classes('text-sm text-secondary mb-2'):
                    ui.icon('calendar_today').classes('inline-block mr-1')
                    ui.label(date_str).classes('inline-block')

                # Time and Score
                with ui.element('div').classes('grid grid-cols-2 gap-md mb-3'):
                    with ui.element('div'):
                        ui.label('Time').classes('text-sm text-secondary')
                        ui.label(race.elapsed_time_formatted).classes('font-bold')

                    with ui.element('div'):
                        ui.label('Score').classes('text-sm text-secondary')
                        score_text = f'{race.score:.1f}' if race.score is not None else '—'
                        ui.label(score_text).classes('font-bold text-success')

                # Actions
                with ui.element('div').classes('flex flex-wrap gap-sm'):
                    ui.link('View Seed', race.permalink.url, new_tab=True).classes('btn btn-sm')

                    if race.runner_vod_url:
                        ui.link('Watch VOD', race.runner_vod_url, new_tab=True).classes('btn btn-sm')

                    if race.discord_thread_id:
                        thread_url = f'https://discord.com/channels/@me/{race.discord_thread_id}'
                        ui.link('Discord Thread', thread_url, new_tab=True).classes('btn btn-sm')
