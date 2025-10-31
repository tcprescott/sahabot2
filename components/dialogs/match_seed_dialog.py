"""Dialog for setting match seed information."""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from components.dialogs.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class MatchSeedDialog(BaseDialog):
    """Dialog for setting or editing match seed information."""

    def __init__(
        self,
        *,
        match_title: str,
        initial_url: str = "",
        initial_description: Optional[str] = None,
        on_submit: Optional[Callable[[str, Optional[str]], None]] = None,
        on_delete: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__()
        self._match_title = match_title
        self._initial_url = initial_url
        self._initial_description = initial_description
        self._on_submit = on_submit
        self._on_delete = on_delete

        # UI refs
        self._url_input: Optional[ui.input] = None
        self._desc_input: Optional[ui.textarea] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(
            title=f'Set Seed for {self._match_title}',
            icon='file_download',
            max_width='dialog-card'
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        with self.create_form_grid(columns=1):
            with ui.element('div'):
                self._url_input = ui.input(
                    label='Seed URL',
                    placeholder='https://example.com/seed.zip',
                    value=self._initial_url
                ).classes('w-full')
            with ui.element('div'):
                self._desc_input = ui.textarea(
                    label='Description (optional)',
                    placeholder='Additional notes about the seed...',
                    value=self._initial_description or ""
                ).classes('w-full')

        with self.create_actions_row():
            # Left side - delete button if seed exists
            if self._initial_url and self._on_delete:
                ui.button('Delete', icon='delete', on_click=self._handle_delete).classes('btn').props('color=negative')
            else:
                ui.element('div')  # Spacer
            
            # Right side - cancel and save
            with ui.row().classes('gap-2'):
                ui.button('Cancel', on_click=self.close).classes('btn')
                ui.button('Save', on_click=self._handle_submit).classes('btn').props('color=positive')

    async def _handle_submit(self) -> None:
        """Handle Save click and call callback."""
        if not self._url_input or not self._url_input.value:
            ui.notify('Seed URL is required', type='warning')
            return
        
        url = self._url_input.value.strip()
        description = self._desc_input.value.strip() if self._desc_input and self._desc_input.value else None
        
        if self._on_submit:
            await self._on_submit(url, description)
        await self.close()

    async def _handle_delete(self) -> None:
        """Handle Delete click and call callback."""
        if self._on_delete:
            await self._on_delete()
        await self.close()
