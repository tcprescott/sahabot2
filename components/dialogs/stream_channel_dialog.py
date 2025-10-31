"""Dialogs for creating and editing Stream Channels."""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from components.dialogs.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class StreamChannelDialog(BaseDialog):
    """Dialog for creating or editing a stream channel."""

    def __init__(
        self,
        *,
        title: str,
        initial_name: str = "",
        initial_stream_url: Optional[str] = None,
        initial_is_active: bool = True,
        on_submit: Optional[Callable[[str, Optional[str], bool], None]] = None,
    ) -> None:
        super().__init__()
        self._title = title
        self._initial_name = initial_name
        self._initial_stream_url = initial_stream_url
        self._initial_is_active = initial_is_active
        self._on_submit = on_submit

        # UI refs
        self._name_input: Optional[ui.input] = None
        self._url_input: Optional[ui.input] = None
        self._active_toggle: Optional[ui.switch] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(title=self._title, icon='cast', max_width='dialog-card')
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        with self.create_form_grid(columns=1):
            with ui.element('div'):
                self._name_input = ui.input(label='Channel Name', value=self._initial_name).classes('w-full')
                with ui.element('div').classes('text-xs text-secondary mt-1'):
                    ui.label('Unique name for this stream channel (e.g., "Main Stream", "Channel 2")')
            with ui.element('div'):
                self._url_input = ui.input(label='Stream URL', value=self._initial_stream_url or "").classes('w-full')
                with ui.element('div').classes('text-xs text-secondary mt-1'):
                    ui.label('Full URL to the stream (e.g., "https://twitch.tv/channel")')
            with ui.element('div'):
                self._active_toggle = ui.switch(text='Active', value=self._initial_is_active)

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save', on_click=self._handle_submit).classes('btn').props('color=positive')

    async def _handle_submit(self) -> None:
        """Handle Save click and call callback."""
        if not self._name_input or not self._name_input.value:
            ui.notify('Channel name is required', type='warning')
            return
        name = self._name_input.value
        stream_url = self._url_input.value if self._url_input else None
        is_active = bool(self._active_toggle.value) if self._active_toggle else True
        if self._on_submit:
            await self._on_submit(name, stream_url, is_active)
        await self.close()
