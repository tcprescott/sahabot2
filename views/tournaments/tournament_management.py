"""
Tournament Management View for tournament admins.

Allows tournament managers to view and manage tournament registrations.
"""

from __future__ import annotations
from nicegui import ui
from models import Organization, User
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs import RegisterPlayerDialog, ConfirmDialog
from application.services.tournament_service import TournamentService
from application.services.organization_service import OrganizationService
import logging

logger = logging.getLogger(__name__)


class TournamentManagementView:
    """View for tournament admins to manage registrations."""

    def __init__(self, organization: Organization, user: User) -> None:
        self.organization = organization
        self.user = user
        self.tournament_service = TournamentService()
        self.org_service = OrganizationService()
        self.container = None
        self.selected_tournament_id = None
        self.registrations_container = None

    async def render(self) -> None:
        """Render the tournament management view."""
        # Check if user has permission to manage tournaments
        can_manage = await self.org_service.user_can_manage_tournaments(
            self.user,
            self.organization.id
        )

        if not can_manage:
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.icon('lock').classes('icon-medium')
                    ui.label('Access Denied').classes('text-xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('You need TOURNAMENT_MANAGER permissions to access this page.').classes('text-secondary')
            return

        self.container = ui.column().classes('w-full gap-md')
        with self.container:
            await self._render_content()

    async def _render_content(self) -> None:
        """Render the main content."""
        # Get all tournaments
        tournaments = await self.tournament_service.list_all_org_tournaments(self.organization.id)

        # Header card
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.icon('emoji_events').classes('icon-medium')
                ui.label('Tournament Management').classes('text-xl font-bold')
            with ui.element('div').classes('card-body'):
                ui.label('Manage tournament registrations for your organization.').classes('text-secondary')

        # Tournament selector
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body'):
                with ui.row().classes('full-width items-center gap-4'):
                    ui.label('Select Tournament:').classes('font-semibold')
                    
                    if not tournaments:
                        ui.label('No tournaments found').classes('text-secondary')
                    else:
                        tournament_options = {t.id: f"{t.name} {'(Active)' if t.is_active else '(Inactive)'}" for t in tournaments}
                        ui.select(
                            label='Tournament',
                            options=tournament_options,
                            value=tournaments[0].id if tournaments else None,
                            on_change=lambda e: self._on_tournament_change(e.value)
                        ).classes('flex-grow')
                        
                        # Set initial selection
                        if tournaments:
                            self.selected_tournament_id = tournaments[0].id

        # Registrations display container
        self.registrations_container = ui.column().classes('w-full')
        with self.registrations_container:
            if self.selected_tournament_id:
                await self._render_registrations(self.selected_tournament_id)

    async def _on_tournament_change(self, tournament_id: int) -> None:
        """Handle tournament selection change."""
        self.selected_tournament_id = tournament_id
        if self.registrations_container:
            self.registrations_container.clear()
            with self.registrations_container:
                await self._render_registrations(tournament_id)

    async def _render_registrations(self, tournament_id: int) -> None:
        """Render the registrations table for a tournament."""
        # Get tournament
        tournaments = await self.tournament_service.list_all_org_tournaments(self.organization.id)
        tournament = next((t for t in tournaments if t.id == tournament_id), None)
        
        if not tournament:
            ui.label('Tournament not found').classes('text-secondary')
            return

        # Get registrations
        registrations = await self.tournament_service.list_tournament_players(
            self.organization.id,
            tournament_id
        )

        async def open_register_dialog():
            """Open dialog to register a new player."""
            dialog = RegisterPlayerDialog(
                admin_user=self.user,
                organization=self.organization,
                tournament=tournament,
                on_save=lambda: self._on_tournament_change(tournament_id)
            )
            await dialog.show()

        async def unregister_player(registration):
            """Unregister a player from the tournament."""
            async def confirm_unregister():
                result = await self.tournament_service.admin_unregister_user_from_tournament(
                    admin_user=self.user,
                    organization_id=self.organization.id,
                    tournament_id=tournament_id,
                    user_id=registration.user_id
                )
                if result:
                    ui.notify('Player unregistered successfully', type='positive')
                    await self._on_tournament_change(tournament_id)
                else:
                    ui.notify('Failed to unregister player', type='negative')

            dialog = ConfirmDialog(
                title='Unregister Player',
                message=f'Are you sure you want to unregister {registration.user.discord_username} from this tournament?',
                on_confirm=confirm_unregister
            )
            await dialog.show()

        with Card.create(title=f'Registered Players ({len(registrations)})'):
            # Action button
            with ui.row().classes('full-width justify-end mb-4'):
                ui.button('Register Player', icon='person_add', on_click=open_register_dialog).classes('btn btn-primary')

            if not registrations:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('people_outline').classes('text-secondary icon-large')
                    ui.label('No players registered yet').classes('text-secondary')
                    ui.label('Click "Register Player" to add players to this tournament').classes('text-secondary text-sm')
            else:
                def render_username(reg):
                    ui.label(reg.user.discord_username)

                def render_registered_date(reg):
                    from components.datetime_label import DateTimeLabel
                    DateTimeLabel.datetime(reg.created_at)

                def render_actions(reg):
                    ui.button(
                        icon='person_remove',
                        on_click=lambda r=reg: unregister_player(r)
                    ).classes('btn btn-sm').props('flat color=negative')

                columns = [
                    TableColumn('Username', cell_render=render_username),
                    TableColumn('Registered', cell_render=render_registered_date),
                    TableColumn('Actions', cell_render=render_actions),
                ]

                table = ResponsiveTable(columns, registrations)
                await table.render()

    async def _refresh(self) -> None:
        """Refresh the entire view."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()
