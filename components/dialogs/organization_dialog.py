"""
Organization dialog for creating and editing organizations.

Extends BaseDialog and supports both create and edit modes.
"""

from __future__ import annotations
from typing import Optional, Callable, Awaitable
from nicegui import ui
from components.dialogs.base_dialog import BaseDialog
from models import Organization
from application.services.organization_service import OrganizationService


class OrganizationDialog(BaseDialog):
    """Dialog for creating or editing an Organization."""

    def __init__(self, organization: Optional[Organization] = None, on_save: Optional[Callable[[], Awaitable[None]]] = None) -> None:
        super().__init__()
        self.organization = organization
        self.on_save = on_save
        self.name_input: Optional[ui.input] = None
        self.desc_input: Optional[ui.input] = None
        self.active_toggle: Optional[ui.switch] = None
        self.service = OrganizationService()

    async def show(self) -> None:
        """Display the dialog in create or edit mode."""
        title = 'Create Organization' if self.organization is None else f"Edit {self.organization.name}"
        self.create_dialog(title=title, icon='domain')
        await super().show()

    def _render_body(self) -> None:
        """Render the form fields for the organization."""
        with self.create_form_grid(columns=2):
            with ui.element('div'):
                self.name_input = ui.input(label='Name', value=self.organization.name if self.organization else '').classes('w-full')
            with ui.element('div'):
                self.active_toggle = ui.switch(text='Active', value=True if self.organization is None else self.organization.is_active)
        with ui.element('div').classes('mt-1'):
            # NiceGUI's input supports .props for multi-line via Quasar
            self.desc_input = ui.input(label='Description', value=self.organization.description if self.organization else '').props('type=textarea autogrow').classes('w-full')

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save' if self.organization else 'Create', on_click=self._save).props('color=positive').classes('btn')

    async def _save(self) -> None:
        """Persist changes and close dialog."""
        name = (self.name_input.value if self.name_input else '').strip()
        description = (self.desc_input.value if self.desc_input else '').strip() if self.desc_input else None
        is_active = bool(self.active_toggle.value) if self.active_toggle else True

        if not name:
            ui.notify('Name is required', color='negative')
            return

        if self.organization is None:
            await self.service.create_organization(name=name, description=description, is_active=is_active)
        else:
            await self.service.update_organization(self.organization.id, name=name, description=description, is_active=is_active)

        if self.on_save:
            await self.on_save()
        await self.close()
