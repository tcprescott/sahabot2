"""Dialog for creating organization invite links."""

from __future__ import annotations
from typing import Optional, Callable
from datetime import datetime, timedelta
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class OrganizationInviteDialog(BaseDialog):
    """Dialog for creating an organization invite link."""

    def __init__(
        self,
        *,
        on_submit: Optional[Callable[[str, Optional[int], Optional[datetime]], None]] = None,
    ) -> None:
        super().__init__()
        self._on_submit = on_submit

        # UI refs
        self._slug_input: Optional[ui.input] = None
        self._max_uses_input: Optional[ui.input] = None
        self._expires_toggle: Optional[ui.switch] = None
        self._expires_days_input: Optional[ui.input] = None

    async def show(self) -> None:
        """Display the dialog."""
        self.create_dialog(title='Create Invite Link', icon='link', max_width='dialog-card')
        await super().show()

    def _render_body(self) -> None:
        """Render dialog body with form fields."""
        with self.create_form_grid(columns=1):
            with ui.element('div'):
                self._slug_input = ui.input(label='Invite Link URL', placeholder='my-tournament-2025').classes('w-full')
                with ui.element('div').classes('text-xs text-secondary mt-1'):
                    ui.label('Choose a unique URL slug (letters, numbers, hyphens, underscores only)')
                with ui.element('div').classes('text-xs text-secondary'):
                    ui.label('Full URL will be: /invite/your-slug-here')
            
            with ui.element('div'):
                self._max_uses_input = ui.input(label='Maximum Uses (optional)', placeholder='Leave empty for unlimited').classes('w-full')
                with ui.element('div').classes('text-xs text-secondary mt-1'):
                    ui.label('Limit how many people can use this invite')
            
            with ui.element('div'):
                self._expires_toggle = ui.switch(text='Set expiration', value=False)
                self._expires_days_input = ui.input(label='Expires in (days)', value='7', placeholder='7').classes('w-full')
                self._expires_days_input.visible = False
                
                def toggle_expiry():
                    self._expires_days_input.visible = self._expires_toggle.value
                
                self._expires_toggle.on_value_change(toggle_expiry)

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Create Invite', on_click=self._handle_submit).classes('btn').props('color=positive')

    async def _handle_submit(self) -> None:
        """Handle Create click and call callback."""
        if not self._slug_input or not self._slug_input.value:
            ui.notify('Invite URL slug is required', type='warning')
            return
        
        slug = self._slug_input.value.strip()
        
        # Parse max uses
        max_uses = None
        if self._max_uses_input and self._max_uses_input.value:
            try:
                max_uses = int(self._max_uses_input.value)
                if max_uses <= 0:
                    ui.notify('Maximum uses must be positive', type='warning')
                    return
            except ValueError:
                ui.notify('Maximum uses must be a number', type='warning')
                return
        
        # Parse expiration
        expires_at = None
        if self._expires_toggle and self._expires_toggle.value:
            if self._expires_days_input and self._expires_days_input.value:
                try:
                    days = int(self._expires_days_input.value)
                    if days <= 0:
                        ui.notify('Expiration days must be positive', type='warning')
                        return
                    expires_at = datetime.now() + timedelta(days=days)
                except ValueError:
                    ui.notify('Expiration days must be a number', type='warning')
                    return
        
        if self._on_submit:
            await self._on_submit(slug, max_uses, expires_at)
        await self.close()
