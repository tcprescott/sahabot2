"""
Admin Global Settings view: manage application-wide settings.

Renders within the Admin page dynamic content area.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from components.card import Card
from components.dialogs import GlobalSettingDialog
from application.services.core.settings_service import SettingsService


class AdminSettingsView:
    """Admin view for managing global application settings."""

    def __init__(self, user: Any) -> None:
        self.user = user
        self.service = SettingsService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the view by re-rendering content in place."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _open_create(self) -> None:
        dialog = GlobalSettingDialog(on_save=self._refresh)
        await dialog.show()

    async def _open_edit(self, key: str, value: Any, description: str, is_public: bool) -> None:
        dialog = GlobalSettingDialog(key=key, value=value, description=description, is_public=is_public, on_save=self._refresh)
        await dialog.show()

    async def _delete_setting(self, key: str) -> None:
        """Confirm and delete a setting by key."""
        confirm = ui.dialog()
        with confirm:
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Delete Setting').classes('text-lg font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label(f"Are you sure you want to delete '{key}'?")
                    with ui.row().classes('dialog-actions'):
                        ui.button('Cancel', on_click=confirm.close).classes('btn')

                        async def do_delete() -> None:
                            await self.service.delete_global(key)
                            confirm.close()
                            await self._refresh()

                        ui.button('Delete', on_click=do_delete).props('color=negative').classes('btn')
        confirm.open()

    async def _render_content(self) -> None:
        """Render the global settings table and controls."""
        settings = await self.service.list_global()

        with Card.create(title='Global Settings'):
            with ui.row().classes('w-full justify-between'):
                ui.label('Manage application-wide configuration settings.')
                ui.button('Create Setting', icon='add', on_click=self._open_create).props('color=positive').classes('btn')

            def render_public(s):
                return ui.icon('public').classes('text-positive') if getattr(s, 'is_public', False) else ui.icon('lock').classes('text-secondary')

            def render_actions(s):
                with ui.element('div').classes('flex gap-2'):
                    ui.button('Edit', icon='edit', on_click=lambda s=s: self._open_edit(s.key, s.value, s.description or '', getattr(s, 'is_public', False))).classes('btn')
                    ui.button('Delete', icon='delete', on_click=lambda s=s: self._delete_setting(s.key)).classes('btn')

            columns = [
                TableColumn('Key', key='key'),
                TableColumn('Value', cell_render=lambda s: ui.label(str(getattr(s, 'value', '') or '')).classes('truncate max-w-64')),
                TableColumn('Public', cell_render=render_public),
                TableColumn('Updated', key='updated_at'),
                TableColumn('Actions', cell_render=render_actions),
            ]
            table = ResponsiveTable(columns, settings)
            await table.render()


    async def render(self) -> None:
        """Render the global settings admin UI."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
