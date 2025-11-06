"""Dialogs for creating and editing Tournaments."""

from __future__ import annotations
from typing import Optional, Callable
import asyncio
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
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
        initial_tracker_enabled: bool = True,
        on_submit: Optional[Callable] = None,
    ) -> None:
        super().__init__()
        self._title = title
        self._initial_name = initial_name
        self._initial_description = initial_description
        self._initial_is_active = initial_is_active
        self._initial_tracker_enabled = initial_tracker_enabled
        self._on_submit = on_submit

        # UI refs
        self._name_input: Optional[ui.input] = None
        self._desc_input: Optional[ui.textarea] = None
        self._active_toggle: Optional[ui.switch] = None
        self._tracker_toggle: Optional[ui.switch] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(title=self._title, icon='emoji_events', max_width='600px')
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        # Basic Settings
        with self.create_form_grid(columns=1):
            with ui.element('div'):
                self._name_input = ui.input(label='Name', value=self._initial_name).classes('w-full')
                ui.label('Tournament name (e.g., "Summer 2025 Championship")').classes('text-xs text-secondary mt-1')
            
            with ui.element('div'):
                self._desc_input = ui.textarea(label='Description', value=self._initial_description or "").classes('w-full')
                ui.label('Optional description visible to players').classes('text-xs text-secondary mt-1')
            
            with ui.element('div'):
                self._active_toggle = ui.checkbox(text='Active', value=self._initial_is_active)
                ui.label('Inactive tournaments are hidden from players').classes('text-xs text-secondary mt-1')
            
            with ui.element('div'):
                self._tracker_toggle = ui.checkbox(text='Enable Tracker Role', value=self._initial_tracker_enabled)
                ui.label('Allows players to request tracker role for notifications').classes('text-xs text-secondary mt-1')

        # Info about additional settings
        ui.separator().classes('my-4')
        with ui.row().classes('items-start gap-2 p-3 rounded bg-info text-white'):
            ui.icon('info')
            with ui.column().classes('gap-1'):
                ui.label('Additional Settings').classes('font-bold')
                ui.label('Configure RaceTime integration, Discord events, and other settings after creating the tournament').classes('text-sm')

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
        tracker_enabled = bool(self._tracker_toggle.value) if self._tracker_toggle else True

        if self._on_submit:
            await self._on_submit(
                name=name,
                description=description,
                is_active=is_active,
                tracker_enabled=tracker_enabled,
            )
        await self.close()


class ConfirmDialog(BaseDialog):
    """Generic confirmation dialog with message and confirm action.
    
    Supports two usage patterns:
    1. Callback pattern: Pass on_confirm callback, dialog handles the action
    2. Awaitable result pattern: Await show() and check result attribute
    """

    def __init__(self, title: str, message: str, on_confirm: Optional[Callable[[], None]] = None) -> None:
        super().__init__()
        self._title = title
        self._message = message
        self._on_confirm = on_confirm
        self.result: bool = False  # True if confirmed, False if cancelled
        self._closed_event = asyncio.Event()

    async def show(self) -> bool:
        """Show the dialog and wait for user response.
        
        Returns:
            bool: True if user confirmed, False if cancelled
        """
        self.create_dialog(title=self._title, icon='help', max_width='dialog-card-sm')
        await super().show()
        
        # Wait for dialog to close
        await self._closed_event.wait()
        
        return self.result

    def _render_body(self) -> None:
        ui.label(self._message).classes('mb-2')
        with self.create_actions_row():
            ui.button('Cancel', on_click=self._handle_cancel).classes('btn')
            ui.button('Confirm', on_click=self._handle_confirm).classes('btn').props('color=negative')

    async def _handle_cancel(self) -> None:
        """Handle cancel button click."""
        self.result = False
        await self.close()
        self._closed_event.set()

    async def _handle_confirm(self) -> None:
        """Handle confirm button click."""
        self.result = True
        if self._on_confirm:
            await self._on_confirm()
        await self.close()
        self._closed_event.set()
