"""
UserEditDialog component for editing user information and permissions.

This dialog belongs to the presentation layer and delegates all business logic
to services in application/services.
"""

from __future__ import annotations
from typing import Optional, Callable
from nicegui import ui
from models import User, Permission
from application.services.user_service import UserService
from application.services.authorization_service import AuthorizationService
from application.services.audit_service import AuditService
from components.dialogs.common.base_dialog import BaseDialog
import logging

logger = logging.getLogger(__name__)


class UserEditDialog(BaseDialog):
    """Dialog for editing user information and permissions."""

    def __init__(
        self,
        target_user: User,
        current_user: User,
        on_save: Optional[Callable] = None,
    ):
        """Initialize user edit dialog.

        Args:
            target_user: User to edit
            current_user: Currently logged in user
            on_save: Callback to execute after successful save
        """
        super().__init__()
        self.target_user = target_user
        self.current_user = current_user
        self.on_save = on_save
        self.user_service = UserService()
        self.auth_service = AuthorizationService()
        self.audit_service = AuditService()

        # State
        self.is_active = target_user.is_active
        self.permission = target_user.permission

    async def show(self) -> None:
        """Display the edit dialog using BaseDialog structure."""
        self.create_dialog(
            title=f'Edit User: {self.target_user.discord_username}',
            icon='edit',
        )
        await super().show()

    def _render_body(self) -> None:
        """Render the dialog body content."""
        with ui.column().classes('full-width gap-md'):
            # User info (read-only)
            self.create_section_title('User Information')
            self.create_info_row('Discord ID', str(self.target_user.discord_id))
            self.create_info_row('Username', self.target_user.discord_username)
            if self.target_user.discord_email:
                self.create_info_row('Email', self.target_user.discord_email)

            ui.separator()

            # Editable fields
            self.create_section_title('Account Status')
            status_switch = ui.switch('Active Account', value=self.is_active)
            status_switch.on('update:model-value', lambda e: setattr(self, 'is_active', e.args))

            # Permission level (only if user can change permissions)
            if self.auth_service.can_change_permissions(self.current_user, self.target_user, Permission.USER):
                self.create_section_title('Permission Level')
                self.create_permission_select(
                    current_permission=self.permission,
                    max_permission=self.current_user.permission,
                    on_change=lambda p: setattr(self, 'permission', p),
                )
            else:
                self.create_info_row('Permission', self.target_user.permission.name)

            ui.separator()

            # Actions
            with self.create_actions_row():
                # Neutral/negative action on the far left
                ui.button('Cancel', on_click=self.close).classes('btn')
                # Positive action on the far right
                ui.button('Save Changes', on_click=self._save_and_close).classes('btn').props('color=positive')

    async def _save_and_close(self) -> None:
        """Save changes and close dialog."""
        try:
            # Check if changes were made
            changed = False
            changes: list[str] = []

            # Update active status
            if self.is_active != self.target_user.is_active:
                if self.is_active:
                    await self.user_service.activate_user(self.target_user.id)
                    changes.append('activated account')
                else:
                    await self.user_service.deactivate_user(self.target_user.id)
                    changes.append('deactivated account')
                changed = True

            # Update permission
            if self.permission != self.target_user.permission:
                if self.auth_service.can_change_permissions(self.current_user, self.target_user, self.permission):
                    await self.user_service.update_user_permission(self.target_user.id, self.permission)
                    changes.append(f'changed permission to {self.permission.name}')
                    changed = True
                else:
                    ui.notify('You do not have permission to change this user\'s permissions', type='negative')
                    return

            if changed:
                # Log the audit entry
                await self.audit_service.log_user_update(
                    user=self.current_user,
                    target_user_id=self.target_user.id,
                    changes=', '.join(changes),
                )

                ui.notify(f'User {self.target_user.discord_username} updated successfully', type='positive')

                # Call the callback
                if self.on_save:
                    await self.on_save()
            else:
                ui.notify('No changes made', type='info')

            await self.close()

        except Exception as e:
            logger.error("Error updating user: %s", e, exc_info=True)
            ui.notify(f'Error updating user: {str(e)}', type='negative')
