"""
Async Tournament Live Races View.

Shows all live races for a tournament with management UI.
"""

from __future__ import annotations
from typing import Optional
from nicegui import ui
from models import User
from models.async_tournament import AsyncTournament, AsyncTournamentLiveRace
from components.card import Card
from components.badge import Badge
from components.empty_state import EmptyState
from components.datetime_label import DateTimeLabel
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs.tournaments import CreateLiveRaceDialog
from components.dialogs.common import ConfirmDialog
from application.services.tournaments.async_live_race_service import AsyncLiveRaceService
from application.services.tournaments.async_tournament_service import AsyncTournamentService
import logging

logger = logging.getLogger(__name__)


class AsyncLiveRacesView:
    """View for async tournament live races with management capabilities."""

    def __init__(self, user: User, tournament: AsyncTournament):
        """
        Initialize the live races view.

        Args:
            user: Current user
            tournament: Tournament to show races for
        """
        self.user = user
        self.tournament = tournament
        self.service = AsyncLiveRaceService()
        self.tournament_service = AsyncTournamentService()
        self.can_manage = False
        self.container: Optional[ui.element] = None
        self.status_filter = 'all'

    async def render(self):
        """Render the live races view."""
        # Check management permissions
        self.can_manage = await self.tournament_service.can_manage_async_tournaments(
            self.user,
            self.tournament.organization_id
        )

        with Card.create(title=f'{self.tournament.name} - Live Races'):
            # Management buttons
            if self.can_manage:
                with ui.row().classes('gap-2 mb-3'):
                    ui.button(
                        'Schedule Live Race',
                        icon='event',
                        on_click=self._show_create_dialog
                    ).classes('btn-primary')

            # Status filter
            with ui.row().classes('gap-2 mb-3'):
                ui.label('Filter:').classes('text-bold')
                filter_options = {
                    'all': 'All',
                    'scheduled': 'Scheduled',
                    'pending': 'Pending',
                    'in_progress': 'In Progress',
                    'finished': 'Finished',
                    'cancelled': 'Cancelled',
                }
                ui.select(
                    options=filter_options,
                    value='all',
                    on_change=lambda e: self._on_filter_change(e.value)
                ).classes('w-48')

            # Container for races
            self.container = ui.element('div')
            await self._refresh_races()

    async def _refresh_races(self):
        """Refresh the live races display."""
        if not self.container:
            return

        self.container.clear()

        with self.container:
            # Get races for tournament
            all_races = await self.service.list_live_races(
                organization_id=self.tournament.organization_id,
                tournament_id=self.tournament.id,
            )

            # Apply status filter
            if self.status_filter != 'all':
                races = [r for r in all_races if r.status == self.status_filter]
            else:
                races = all_races

            if not races:
                EmptyState.no_items(
                    item_name='live races',
                    message='No live races match your filters',
                    icon='event_busy',
                    in_card=False
                )
                return

            # Render races table
            await self._render_races_table(races)

    async def _render_races_table(self, races: list[AsyncTournamentLiveRace]):
        """Render races in a responsive table."""
        # Define columns
        columns = [
            TableColumn(label='Status', key='status', cell_render=self._render_status_badge),
            TableColumn(label='Scheduled', key='scheduled_at', cell_render=self._render_scheduled),
            TableColumn(label='Pool', key='pool'),
            TableColumn(label='Title', key='match_title'),
            TableColumn(label='RaceTime.gg', key='racetime_url', cell_render=self._render_racetime_link),
        ]

        # Add actions column if user can manage
        if self.can_manage:
            columns.append(TableColumn(label='Actions', key='id', cell_render=self._render_actions))

        # Create table
        table = ResponsiveTable(columns=columns, rows=races)
        await table.render()

    def _render_status_badge(self, race: AsyncTournamentLiveRace):
        """Render status badge."""
        status_variants = {
            'scheduled': 'info',
            'pending': 'warning',
            'in_progress': 'info',
            'finished': 'success',
            'cancelled': 'danger',
        }
        variant = status_variants.get(race.status, 'default')
        text = race.status.replace('_', ' ').title()
        
        with ui.element('div'):
            Badge.custom(text, variant)

    def _render_scheduled(self, race: AsyncTournamentLiveRace):
        """Render scheduled datetime."""
        with ui.element('div'):
            DateTimeLabel.create(race.scheduled_at, format_type='datetime')

    async def _render_pool(self, race: AsyncTournamentLiveRace):
        """Render pool name."""
        await race.fetch_related('pool')
        with ui.element('div'):
            ui.label(race.pool.name if race.pool else 'N/A')

    def _render_racetime_link(self, race: AsyncTournamentLiveRace):
        """Render RaceTime.gg link if available."""
        with ui.element('div'):
            if race.racetime_url:
                ui.link('View Race', race.racetime_url, new_tab=True)
            else:
                ui.label('Not opened yet').classes('text-secondary')

    def _render_actions(self, race: AsyncTournamentLiveRace):
        """Render action buttons."""
        with ui.row().classes('gap-1'):
            # View eligible participants
            ui.button(
                icon='people',
                on_click=lambda r=race: self._view_eligible_participants(r)
            ).classes('btn-sm').props('flat').tooltip('View Eligible Participants')

            # Cancel (if not finished)
            if race.status not in ('finished', 'cancelled'):
                ui.button(
                    icon='cancel',
                    on_click=lambda r=race: self._confirm_cancel_race(r)
                ).classes('btn-sm text-warning').props('flat').tooltip('Cancel Race')

            # Delete (if scheduled or cancelled)
            if race.status in ('scheduled', 'cancelled'):
                ui.button(
                    icon='delete',
                    on_click=lambda r=race: self._confirm_delete_race(r)
                ).classes('btn-sm text-danger').props('flat').tooltip('Delete Race')

    async def _show_create_dialog(self):
        """Show dialog for creating a live race."""
        # Get tournament data
        await self.tournament.fetch_related('pools', 'permalinks')

        # Get race room profiles
        from application.services.racetime.race_room_profile_service import RaceRoomProfileService
        profile_service = RaceRoomProfileService()
        profiles = await profile_service.list_profiles(
            current_user=self.user,
            organization_id=self.tournament.organization_id,
        )

        dialog = CreateLiveRaceDialog(
            organization_id=self.tournament.organization_id,
            tournament_id=self.tournament.id,
            pools=self.tournament.pools,
            permalinks=self.tournament.permalinks,
            profiles=profiles,
            on_save=self._refresh_races,
        )
        await dialog.show()

    async def _view_eligible_participants(self, race: AsyncTournamentLiveRace):
        """Show dialog with eligible participants for this race."""
        # Get eligible participants
        participants = await self.service.get_eligible_participants(
            organization_id=self.tournament.organization_id,
            live_race_id=race.id,
        )

        # Show dialog
        with ui.dialog() as dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('people').classes('icon-medium')
                        ui.label('Eligible Participants').classes('text-xl text-bold')

                # Body
                with ui.element('div').classes('card-body'):
                    if not participants:
                        ui.label('No eligible participants').classes('text-secondary')
                    else:
                        with ui.column().classes('gap-2'):
                            for participant in participants:
                                with ui.row().classes('items-center gap-2'):
                                    ui.icon('person', size='sm')
                                    ui.label(participant.discord_username)

                    # Close button
                    with ui.row().classes('justify-end mt-4'):
                        ui.button('Close', on_click=dialog.close).classes('btn')

        dialog.open()

    async def _confirm_cancel_race(self, race: AsyncTournamentLiveRace):
        """Confirm cancelling a race."""
        async def on_confirm():
            try:
                await self.service.cancel_live_race(
                    current_user=self.user,
                    organization_id=self.tournament.organization_id,
                    live_race_id=race.id,
                    reason='Cancelled by admin',
                )
                await self._refresh_races()
            except Exception as e:
                logger.error("Failed to cancel race: %s", e, exc_info=True)
                ui.notify(f"Failed to cancel race: {e}", type='negative')

        dialog = ConfirmDialog(
            title='Cancel Race',
            message='Are you sure you want to cancel this race?',
            on_confirm=on_confirm,
        )
        await dialog.show()

    async def _confirm_delete_race(self, race: AsyncTournamentLiveRace):
        """Confirm deleting a race."""
        async def on_confirm():
            try:
                await self.service.delete_live_race(
                    current_user=self.user,
                    organization_id=self.tournament.organization_id,
                    live_race_id=race.id,
                )
                await self._refresh_races()
            except Exception as e:
                logger.error("Failed to delete race: %s", e, exc_info=True)
                ui.notify(f"Failed to delete race: {e}", type='negative')

        dialog = ConfirmDialog(
            title='Delete Race',
            message='Are you sure you want to delete this race? This action cannot be undone.',
            on_confirm=on_confirm,
        )
        await dialog.show()

    async def _on_filter_change(self, status: str):
        """Handle status filter change."""
        self.status_filter = status
        await self._refresh_races()
