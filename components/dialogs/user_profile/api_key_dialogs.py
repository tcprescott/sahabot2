"""
Dialogs for API key management.

This module provides dialog components for creating and displaying API keys.
"""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class CreateApiKeyDialog(BaseDialog):
    """Dialog for creating a new API key - also displays the generated token."""

    def __init__(self, on_create: Optional[Callable[[str], None]] = None, on_complete: Optional[Callable[[], None]] = None):
        """Initialize the create API key dialog.

        Args:
            on_create: Callback function to call with the key name when created, should return the token
            on_complete: Callback function to call when dialog is completely done
        """
        super().__init__()
        self.on_create = on_create
        self.on_complete = on_complete
        self.name_input: Optional[ui.input] = None
        self.generated_token: Optional[str] = None
        self.body_container: Optional[ui.element] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title='Generate New API Key',
            icon='add_circle',
            max_width='dialog-card',
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog content."""
        self.body_container = ui.column().classes('w-full gap-md')
        with self.body_container:
            self._render_create_form()

    def _render_create_form(self) -> None:
        """Render the initial create form."""
        ui.label('Create a new API key for accessing the SahaBot API.').classes('text-secondary mb-2')

        with self.create_form_grid(columns=1):
            with ui.element('div'):
                self.name_input = ui.input(label='Key Name', placeholder='e.g., "Production Bot"').classes('w-full')
                self.name_input.on('keydown.enter', self._handle_create)

        # Actions
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Generate', on_click=self._handle_create).classes('btn').props('color=positive')

    def _render_token_display(self) -> None:
        """Render the token display after generation."""
        # Warning message
        with ui.element('div').classes('alert alert-warning mb-4'):
            with ui.row().classes('items-center gap-sm'):
                ui.icon('warning').classes('icon-medium')
                ui.label('Save this token now! You won\'t be able to see it again.').classes('text-bold')

        # Token display with copy button
        with ui.row().classes('w-full items-center gap-2'):
            ui.input(value=self.generated_token).props('readonly').classes('flex-1 font-mono text-sm')
            
            async def copy_token():
                success = await ui.run_javascript(
                    f'return window.ClipboardUtils.copy("{self.generated_token}");'
                )
                if success:
                    ui.notify('Token copied to clipboard', type='positive')
                else:
                    ui.notify('Failed to copy token', type='negative')
            
            ui.button(icon='content_copy', on_click=copy_token).props('flat').classes('btn')

        # Close button
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Close', on_click=self._handle_close).classes('btn').props('color=primary')

    async def _handle_create(self) -> None:
        """Handle create button click."""
        if not self.name_input or not self.name_input.value:
            ui.notify('Please enter a key name', type='warning')
            return

        if self.on_create:
            self.generated_token = await self.on_create(self.name_input.value)

            # Update dialog to show token
            if self.generated_token and self.body_container:
                self.body_container.clear()
                with self.body_container:
                    self._render_token_display()

    async def _handle_close(self) -> None:
        """Handle close after token is displayed."""
        if self.on_complete:
            await self.on_complete()
        await self.close()


class DisplayTokenDialog(BaseDialog):
    """Dialog for displaying a newly generated API token (one-time display)."""

    def __init__(self, token: str):
        """Initialize the display token dialog.

        Args:
            token: The plaintext API token to display
        """
        super().__init__()
        self.token = token

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title='API Key Generated',
            icon='key',
            max_width='dialog-card',
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog content."""
        # Warning message
        with ui.element('div').classes('alert alert-warning mb-4'):
            with ui.row().classes('items-center gap-sm'):
                ui.icon('warning').classes('icon-medium')
                ui.label('Save this token now! You won\'t be able to see it again.').classes('text-bold')

        # Token display with copy button
        with ui.row().classes('w-full items-center gap-2'):
            ui.input(value=self.token).props('readonly').classes('flex-1 font-mono text-sm')
            
            async def copy_token():
                success = await ui.run_javascript(
                    f'return window.ClipboardUtils.copy("{self.token}");'
                )
                if success:
                    ui.notify('Token copied to clipboard', type='positive')
                else:
                    ui.notify('Failed to copy token', type='negative')
            
            ui.button(icon='content_copy', on_click=copy_token).props('flat').classes('btn')

        # Close button
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Close', on_click=self.close).classes('btn').props('color=primary')
