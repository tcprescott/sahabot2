"""
Organization Settings view.

Configure organization settings and preferences.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization
from components.card import Card
from components.dialogs import OrganizationDialog, OrgSettingDialog
from application.services.organization_service import OrganizationService
from application.services.settings_service import SettingsService
from components.data_table import ResponsiveTable, TableColumn


class OrganizationSettingsView:
    """Manage organization settings."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user
        self.service = OrganizationService()
        self.settings_service = SettingsService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the organization data and re-render."""
        # Reload organization from database
        updated_org = await self.service.get_organization(self.organization.id)
        if updated_org:
            self.organization = updated_org
        
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _open_edit_dialog(self) -> None:
        """Open the organization edit dialog."""
        dialog = OrganizationDialog(organization=self.organization, on_save=self._refresh)
        await dialog.show()

    async def _render_content(self) -> None:
        """Render the settings content."""
        # Basic info card
        with Card.create(title='Organization Information'):
            with ui.column().classes('gap-md'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('Basic Settings').classes('text-lg font-semibold')
                    ui.button('Edit', icon='edit', on_click=self._open_edit_dialog).classes('btn')
                
                ui.separator()
                
                with ui.row().classes('gap-md'):
                    ui.label('Name:').classes('font-semibold')
                    ui.label(self.organization.name)
                
                with ui.row().classes('gap-md'):
                    ui.label('Description:').classes('font-semibold')
                    ui.label(self.organization.description or 'No description')
                
                with ui.row().classes('gap-md'):
                    ui.label('Status:').classes('font-semibold')
                    if self.organization.is_active:
                        with ui.row().classes('items-center gap-sm'):
                            ui.icon('check_circle').classes('text-positive')
                            ui.label('Active')
                    else:
                        with ui.row().classes('items-center gap-sm'):
                            ui.icon('cancel').classes('text-negative')
                            ui.label('Inactive')
        
        # Organization-specific settings management
        await self._render_org_settings()

    async def _render_org_settings(self) -> None:
        """Render organization-specific settings list and controls."""
        items = await self.settings_service.list_org(self.organization.id)

        with Card.create(title='Organization Settings', classes='mt-2'):
            with ui.row().classes('w-full justify-between'):
                ui.label('Manage configuration overrides for this organization.')

                async def open_create() -> None:
                    await self._open_create_setting()

                ui.button('Add Setting', icon='add', on_click=open_create).props('color=positive').classes('btn')

            def render_actions(s):
                with ui.element('div').classes('flex gap-2'):

                    async def open_edit() -> None:
                        await self._open_edit_setting(s.key, s.value, s.description or '')

                    async def delete_item() -> None:
                        await self._delete_setting(s.key)

                    ui.button('Edit', icon='edit', on_click=open_edit).classes('btn')
                    ui.button('Delete', icon='delete', on_click=delete_item).classes('btn')

            columns = [
                TableColumn('Key', key='key'),
                TableColumn('Value', cell_render=lambda s: ui.label(str(getattr(s, 'value', '') or '')).classes('truncate max-w-64')),
                TableColumn('Updated', key='updated_at'),
                TableColumn('Actions', cell_render=render_actions),
            ]
            table = ResponsiveTable(columns, items)
            await table.render()

    async def _open_create_setting(self) -> None:
        dialog = OrgSettingDialog(organization_id=self.organization.id, on_save=self._refresh)
        await dialog.show()

    async def _open_edit_setting(self, key: str, value: Any, description: str) -> None:
        dialog = OrgSettingDialog(organization_id=self.organization.id, key=key, value=value, description=description, on_save=self._refresh)
        await dialog.show()

    async def _delete_setting(self, key: str) -> None:
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
                            await self.settings_service.delete_org(self.organization.id, key)
                            confirm.close()
                            await self._refresh()

                        ui.button('Delete', on_click=do_delete).props('color=negative').classes('btn')
        confirm.open()

    

    async def render(self) -> None:
        """Render the settings view."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
