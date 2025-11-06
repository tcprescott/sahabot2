"""
Dialog for editing the Message of the Day (MOTD).
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from application.services.core.settings_service import SettingsService


class MOTDDialog(BaseDialog):
    """Dialog for editing the Message of the Day banner."""

    MOTD_KEY = 'motd_text'
    MOTD_UPDATED_KEY = 'motd_updated_at'

    def __init__(self, on_save: Optional[Callable[[], Awaitable[None]]] = None) -> None:
        super().__init__()
        self.on_save = on_save
        self.service = SettingsService()
        self.motd_input = None
        self.current_motd = ""

    async def show(self) -> None:
        # Load current MOTD
        motd_setting = await self.service.get_global(self.MOTD_KEY)
        if motd_setting:
            self.current_motd = motd_setting.get('value', '')

        self.create_dialog(title='Edit Message of the Day', icon='campaign')
        await super().show()

    def _render_body(self) -> None:
        with ui.element('div').classes('card-body'):
            ui.label('Customize the message that appears in the banner at the top of pages.').classes('mb-4')
            ui.label('HTML formatting is supported. Leave empty to disable the banner.').classes('mb-4 text-secondary')

            self.motd_input = ui.textarea(
                label='MOTD Message',
                value=self.current_motd,
                placeholder='Enter your message here...'
            ).classes('w-full').props('rows=4 autogrow')

            ui.label('Preview:').classes('mt-4 font-bold')
            with ui.element('div').classes('p-3 rounded').style(
                'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                'color: white;'
            ):
                self.preview_label = ui.html(self.current_motd or '<em>No message set</em>')

            # Update preview when input changes
            def update_preview():
                text = self.motd_input.value or '<em>No message set</em>'
                self.preview_label.set_content(text)

            self.motd_input.on('input', update_preview)

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Save', on_click=self._save).props('color=positive').classes('btn')

    async def _save(self) -> None:
        """Save the MOTD and update the timestamp."""
        motd_text = (self.motd_input.value or '').strip() if self.motd_input else ''

        # Save MOTD text
        await self.service.set_global(
            key=self.MOTD_KEY,
            value=motd_text,
            description='Message of the Day banner text',
            is_public=True  # MOTD is publicly visible
        )

        # Update the timestamp to trigger banner re-display for dismissed users
        current_time = datetime.now(timezone.utc).isoformat()
        await self.service.set_global(
            key=self.MOTD_UPDATED_KEY,
            value=current_time,
            description='Last time MOTD was updated (ISO timestamp)',
            is_public=True
        )

        ui.notify('MOTD updated successfully', type='positive')

        if self.on_save:
            await self.on_save()
        await self.close()
