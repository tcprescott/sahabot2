"""
UserAddDialog component for creating a new user manually.

UI-only dialog that delegates user creation to the UserService.
"""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from models import Permission
from application.services.core.user_service import UserService
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class UserAddDialog(BaseDialog):
    """Dialog for adding a new user manually."""

    def __init__(
        self,
        current_user_permission: Permission,
        on_save: Optional[Callable] = None,
    ) -> None:
        """Initialize the add user dialog.

        Args:
            current_user_permission: Permission level of the current admin (limits assignable permissions)
            on_save: Optional callback invoked after successful creation
        """
        super().__init__()
        self.on_save = on_save
        self.user_service = UserService()
        self.current_user_permission = current_user_permission
        # Form state
        self.discord_id: Optional[int] = None
        self.discord_username: str = ""
        self.discord_email: Optional[str] = None
        self.permission: Permission = Permission.USER
        self.is_active: bool = True

    async def show(self) -> None:
        """Display the add user dialog using BaseDialog structure."""
        self.create_dialog(
            title='Add New User',
            icon='person_add',
        )
        await super().show()

    def _render_body(self) -> None:
        """Render the dialog body content."""
        # Responsive form grid
        with self.create_form_grid(columns=2):
            # Discord ID
            with ui.element('div'):
                discord_id_input = ui.input(label='Discord ID', placeholder='e.g., 123456789012345678').classes('w-full')
                discord_id_input.on('update:model-value', self._on_discord_id_change)

            # Username
            with ui.element('div'):
                username_input = ui.input(label='Username', placeholder='Discord username').classes('w-full')
                username_input.on('update:model-value', lambda e: setattr(self, 'discord_username', e.args))

            # Email (optional) spans full width on desktop
            with ui.element('div').classes('span-2'):
                email_input = ui.input(label='Email (optional)', placeholder='name@example.com').classes('w-full')
                email_input.on('update:model-value', lambda e: setattr(self, 'discord_email', e.args))

            # Permission (cannot assign >= current user's permission)
            with ui.element('div'):
                self.create_permission_select(
                    current_permission=self.permission,
                    max_permission=self.current_user_permission,
                    on_change=lambda p: setattr(self, 'permission', p),
                )

            # Active switch
            with ui.element('div'):
                active_switch = ui.checkbox('Active Account', value=self.is_active)
                active_switch.on('update:model-value', lambda e: setattr(self, 'is_active', e.args))

        ui.separator()

        # Actions
        with self.create_actions_row():
            # Neutral/negative action on the far left
            ui.button('Cancel', on_click=self.close).classes('btn')
            # Positive action on the far right
            ui.button('Create User', on_click=self._create_and_close).classes('btn').props('color=positive')

    def _on_discord_id_change(self, e) -> None:
        """Handle Discord ID change and coerce to int when possible."""
        try:
            self.discord_id = int(str(e.args).strip()) if e.args else None
        except Exception:
            self.discord_id = None

    async def _create_and_close(self) -> None:
        """Create the user through the service, notify, and close dialog."""
        try:
            # Basic validation
            if not self.discord_id or not self.discord_username:
                ui.notify('Discord ID and Username are required', type='warning')
                return

            user = await self.user_service.create_user_manual(
                discord_id=self.discord_id,
                discord_username=self.discord_username,
                discord_email=self.discord_email,
                permission=self.permission,
                is_active=self.is_active,
            )

            ui.notify(f'User {user.discord_username} created', type='positive')
            if self.on_save:
                await self.on_save()
            await self.close()
        except Exception as ex:
            logger.error('Failed to create user: %s', ex, exc_info=True)
            ui.notify(str(ex), type='negative')
