"""
Dialog for creating/updating an organization setting.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable, Any
from nicegui import ui
from components.dialogs.base_dialog import BaseDialog
from application.services.settings_service import SettingsService


class OrgSettingDialog(BaseDialog):
    """Dialog for editing or creating an organization-scoped setting."""

    def __init__(self, organization_id: int, key: Optional[str] = None, value: Optional[Any] = None, description: Optional[str] = None, on_save: Optional[Callable[[], Awaitable[None]]] = None) -> None:
        super().__init__()
        self.organization_id = organization_id
        self.key = key or ""
        self.value = value
        self.description = description or ""
        self.on_save = on_save
        self.service = SettingsService()

        self.key_input = None
        self.value_input = None
        self.desc_input = None
        self.public_switch = None

    async def show(self) -> None:
        title = 'Create Organization Setting' if not self.key else f'Edit Setting: {self.key}'
        self.create_dialog(title=title, icon='tune')
        await super().show()

    def _render_body(self) -> None:
        with self.create_form_grid(columns=2):
            with ui.element('div').classes('span-2'):
                self.key_input = ui.input(label='Key', value=self.key, placeholder='e.g., match_default_duration').classes('w-full')
            with ui.element('div').classes('span-2'):
                self.value_input = ui.input(label='Value', value='' if self.value is None else str(self.value)).props('type=textarea autogrow').classes('w-full')
            with ui.element('div').classes('span-2'):
                self.desc_input = ui.input(label='Description', value=self.description).classes('w-full')
            # Organization settings do not have a public flag; visibility is governed by org permissions
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save', on_click=self._save).props('color=positive').classes('btn')

    async def _save(self) -> None:
        value: str = (self.value_input.value or '') if self.value_input else ''
        await self.service.set_org(
            organization_id=self.organization_id,
            key=(self.key_input.value or '').strip(),
            value=value,
            description=(self.desc_input.value or '').strip() if self.desc_input else None,
        )
        if self.on_save:
            await self.on_save()
        await self.close()
