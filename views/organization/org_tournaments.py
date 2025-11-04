"""
Organization Tournaments view.

List, create, edit, and delete tournaments within an organization.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs import TournamentDialog, ConfirmDialog
from application.services.tournament_service import TournamentService
from application.repositories.racetime_bot_repository import RacetimeBotRepository


class OrganizationTournamentsView:
    """Manage tournaments for an organization."""

    def __init__(self, user: Any, organization: Organization, service: TournamentService) -> None:
        self.user = user
        self.organization = organization
        self.service = service
        self.racetime_bot_repo = RacetimeBotRepository()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh view by clearing and re-rendering."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _open_create_dialog(self) -> None:
        """Open dialog to create a new tournament."""
        # Get available RaceTime bots for this organization
        racetime_bots = await self.racetime_bot_repo.get_bots_for_organization(self.organization.id)
        bot_options = {bot.id: f"{bot.category} ({bot.client_id})" for bot in racetime_bots if bot.is_active}
        
        async def on_submit(**kwargs) -> None:
            await self.service.create_tournament(
                user=self.user,
                organization_id=self.organization.id,
                **kwargs
            )
            await self._refresh()

        dialog = TournamentDialog(
            title='New Tournament',
            on_submit=on_submit,
            initial_is_active=True,
            initial_tracker_enabled=True,
            available_racetime_bots=bot_options,
        )
        await dialog.show()

    async def _open_edit_dialog(self, t) -> None:
        """Open dialog to edit an existing tournament."""
        # Get available RaceTime bots for this organization
        racetime_bots = await self.racetime_bot_repo.get_bots_for_organization(self.organization.id)
        bot_options = {bot.id: f"{bot.category} ({bot.client_id})" for bot in racetime_bots if bot.is_active}
        
        async def on_submit(**kwargs) -> None:
            await self.service.update_tournament(
                user=self.user,
                organization_id=self.organization.id,
                tournament_id=t.id,
                **kwargs
            )
            await self._refresh()

        dialog = TournamentDialog(
            title=f'Edit {getattr(t, "name", "Tournament")}',
            initial_name=getattr(t, 'name', ''),
            initial_description=getattr(t, 'description', None),
            initial_is_active=bool(getattr(t, 'is_active', True)),
            initial_tracker_enabled=bool(getattr(t, 'tracker_enabled', True)),
            available_racetime_bots=bot_options,
            initial_racetime_bot_id=getattr(t, 'racetime_bot_id', None),
            initial_racetime_auto_create=bool(getattr(t, 'racetime_auto_create_rooms', False)),
            initial_room_open_minutes=int(getattr(t, 'room_open_minutes_before', 60)),
            initial_require_racetime_link=bool(getattr(t, 'require_racetime_link', False)),
            initial_racetime_default_goal=getattr(t, 'racetime_default_goal', None),
            on_submit=on_submit,
        )
        await dialog.show()

    async def _confirm_delete(self, t) -> None:
        """Ask for confirmation and delete the tournament if confirmed."""
        async def do_delete() -> None:
            await self.service.delete_tournament(self.user, self.organization.id, t.id)
            await self._refresh()

        dialog = ConfirmDialog(
            title='Delete Tournament',
            message=f"Are you sure you want to delete '{getattr(t, 'name', 'Tournament')}'?",
            on_confirm=do_delete,
        )
        await dialog.show()

    async def _render_content(self) -> None:
        """Render tournaments list and actions."""
        tournaments = await self.service.list_org_tournaments(self.user, self.organization.id)

        with Card.create(title='Tournaments'):
            with ui.row().classes('w-full justify-between mb-2'):
                ui.label(f'{len(tournaments)} tournament(s) in this organization')
                ui.button('New Tournament', icon='add', on_click=self._open_create_dialog).props('color=positive').classes('btn')

            if not tournaments:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('emoji_events').classes('text-secondary icon-large')
                    ui.label('No tournaments yet').classes('text-secondary')
                    ui.label('Click "New Tournament" to create one').classes('text-secondary text-sm')
            else:
                def render_active(t):
                    if getattr(t, 'is_active', False):
                        with ui.row().classes('items-center gap-sm'):
                            ui.icon('check_circle').classes('text-positive')
                            ui.label('Active')
                    else:
                        with ui.row().classes('items-center gap-sm'):
                            ui.icon('cancel').classes('text-negative')
                            ui.label('Inactive')

                def render_actions(t):
                    with ui.element('div').classes('flex gap-2'):
                        ui.button('Edit', icon='edit', on_click=lambda t=t: self._open_edit_dialog(t)).classes('btn')
                        ui.button('Delete', icon='delete', on_click=lambda t=t: self._confirm_delete(t)).classes('btn')

                columns = [
                    TableColumn('Name', key='name'),
                    TableColumn('Description', cell_render=lambda t: ui.label(str(getattr(t, 'description', '') or '')).classes('truncate max-w-64')),
                    TableColumn('Status', cell_render=render_active),
                    TableColumn('Created', key='created_at'),
                    TableColumn('Actions', cell_render=render_actions),
                ]
                table = ResponsiveTable(columns, tournaments)
                await table.render()

    async def render(self) -> None:
        """Render the tournaments view."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
