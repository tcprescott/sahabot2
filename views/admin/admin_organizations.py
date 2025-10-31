"""
Admin Organizations view: list, create, and edit organizations.

Renders within the Admin page dynamic content area.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from components.card import Card
from components.datetime_label import DateTimeLabel
from components.dialogs import OrganizationDialog
from application.services.organization_service import OrganizationService


class AdminOrganizationsView:
    """Admin view for managing organizations."""

    def __init__(self, user: Any) -> None:
        self.user = user
        self.service = OrganizationService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the organization list by re-rendering this view in-place."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the actual content (table and controls)."""
        orgs = await self.service.list_organizations()

        with Card.create(title='Organizations'):
            with ui.row().classes('w-full justify-between'):
                ui.label('Manage organizations: create and edit basic settings.')
                ui.button('Create Organization', icon='add', on_click=self._open_create).props('color=positive').classes('btn')

            columns = [
                TableColumn('Name', key='name'),
                TableColumn('Active', cell_render=lambda o: ui.icon('check_circle').classes('text-positive') if o.is_active else ui.icon('cancel').classes('text-negative')),
                TableColumn('Created', cell_render=lambda o: DateTimeLabel.datetime(o.created_at)),
                TableColumn('Actions', cell_render=lambda o: self._actions_cell(o)),
            ]
            table = ResponsiveTable(columns, orgs)
            await table.render()

    async def render(self) -> None:
        """Render the organizations admin UI."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()

    def _actions_cell(self, org):
        """Render actions for a single organization row."""
        with ui.element('div').classes('flex gap-2'):
            ui.button('Edit', icon='edit', on_click=lambda: self._open_edit(org)).classes('btn')
            ui.button('Manage', icon='settings', on_click=lambda: ui.navigate.to(f'/admin/organizations/{org.id}')).classes('btn')

    async def _open_create(self) -> None:
        dialog = OrganizationDialog(on_save=self._refresh)
        await dialog.show()

    async def _open_edit(self, org) -> None:
        dialog = OrganizationDialog(organization=org, on_save=self._refresh)
        await dialog.show()
