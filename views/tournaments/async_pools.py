"""
Async Tournament Pools View.

Shows all pools and their permalinks for a tournament.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament
from components.card import Card
from application.services.async_tournament_service import AsyncTournamentService


class AsyncPoolsView:
    """View for async tournament pools and permalinks."""

    def __init__(self, user: User, tournament: AsyncTournament):
        self.user = user
        self.tournament = tournament
        self.service = AsyncTournamentService()

    async def render(self):
        """Render the pools view."""
        with Card.create(title=f'{self.tournament.name} - Pools'):
            # Get pools
            await self.tournament.fetch_related('pools', 'pools__permalinks')

            if not self.tournament.pools:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('folder_open').classes('text-secondary icon-large')
                    ui.label('No pools configured yet').classes('text-secondary')
                return

            # Render each pool
            for pool in self.tournament.pools:
                await self._render_pool(pool)

    async def _render_pool(self, pool):
        """Render a single pool section."""
        with ui.element('div').classes('card mb-4'):
            # Pool header
            with ui.element('div').classes('card-header'):
                ui.element('h5').classes('').add_slot('default', pool.name)
                if pool.description:
                    ui.label(pool.description).classes('text-sm text-secondary')

            # Pool permalinks
            with ui.element('div').classes('card-body'):
                if not pool.permalinks:
                    ui.label('No permalinks yet').classes('text-secondary')
                else:
                    with ui.element('ul').classes('list-unstyled'):
                        for permalink in pool.permalinks:
                            with ui.element('li').classes('mb-2'):
                                # Link to permalink details page
                                permalink_link = f'/tournaments/{self.tournament.organization_id}/async/{self.tournament.id}/permalink/{permalink.id}'
                                ui.link(permalink.url, permalink_link)
                                # Show par time if available
                                if permalink.par_time is not None:
                                    ui.label(f' (Par: {permalink.par_time_formatted})').classes('text-sm text-secondary')
