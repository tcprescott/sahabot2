"""Dialogs for creating and editing Tournaments."""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from components.dialogs.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class TournamentDialog(BaseDialog):
    """Dialog for creating or editing a tournament."""

    def __init__(
        self,
        *,
        title: str,
        initial_name: str = "",
        initial_description: Optional[str] = None,
        initial_is_active: bool = True,
        on_submit: Optional[Callable[[str, Optional[str], bool], None]] = None,
    ) -> None:
        super().__init__()
        self._title = title
        self._initial_name = initial_name
        self._initial_description = initial_description
        self._initial_is_active = initial_is_active
        self._on_submit = on_submit

        # UI refs
        self._name_input: Optional[ui.input] = None
        self._desc_input: Optional[ui.textarea] = None
        self._active_toggle: Optional[ui.switch] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(title=self._title, icon='emoji_events', max_width='dialog-card')
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        with self.create_form_grid(columns=1):
            with ui.element('div'):
                self._name_input = ui.input(label='Name', value=self._initial_name).classes('w-full')
            with ui.element('div'):
                self._desc_input = ui.textarea(label='Description', value=self._initial_description or "").classes('w-full')
            with ui.element('div'):
                self._active_toggle = ui.switch(text='Active', value=self._initial_is_active)

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save', on_click=self._handle_submit).classes('btn').props('color=positive')

    async def _handle_submit(self) -> None:
        """Handle Save click and call callback."""
        if not self._name_input or not self._name_input.value:
            ui.notify('Name is required', type='warning')
            return
        name = self._name_input.value
        description = self._desc_input.value if self._desc_input else None
        is_active = bool(self._active_toggle.value) if self._active_toggle else True
        if self._on_submit:
            await self._on_submit(name, description, is_active)
        await self.close()


class ConfirmDialog(BaseDialog):
    """Generic confirmation dialog with message and confirm action."""

    def __init__(self, title: str, message: str, on_confirm: Optional[Callable[[], None]] = None) -> None:
        super().__init__()
        self._title = title
        self._message = message
        self._on_confirm = on_confirm

    async def show(self) -> None:
        self.create_dialog(title=self._title, icon='help', max_width='dialog-card-sm')
        await super().show()

    def _render_body(self) -> None:
        ui.label(self._message).classes('mb-2')
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Confirm', on_click=self._handle_confirm).classes('btn').props('color=negative')

    async def _handle_confirm(self) -> None:
        if self._on_confirm:
            await self._on_confirm()
        await self.close()
