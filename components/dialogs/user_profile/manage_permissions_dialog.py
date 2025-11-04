"""
Manage Permissions Dialog.

Dialog for managing user permissions in a namespace.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import PresetNamespace, PresetNamespacePermission
from components.dialogs.common.base_dialog import BaseDialog
from components.dialogs.common.tournament_dialogs import ConfirmDialog
from components.dialogs.user_profile.add_permission_dialog import AddPermissionDialog
from components.dialogs.user_profile.edit_permission_dialog import EditPermissionDialog

logger = logging.getLogger(__name__)


class ManagePermissionsDialog(BaseDialog):
    """Dialog for managing namespace permissions."""

    def __init__(self, namespace: PresetNamespace, on_close=None):
        """
        Initialize manage permissions dialog.

        Args:
            namespace: Namespace to manage permissions for
            on_close: Callback when dialog closes
        """
        super().__init__()
        self.namespace = namespace
        self.on_close = on_close
        self.permissions = []
        self.permissions_container = None

    async def show(self):
        """Display the dialog."""
        # Fetch existing permissions
        self.permissions = await PresetNamespacePermission.filter(
            namespace_id=self.namespace.id
        ).prefetch_related('user').all()

        self.create_dialog(
            title=f'Manage Permissions: {self.namespace.display_name}',
            icon='people',
            max_width='800px'
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        ui.label('Delegated Users').classes('font-bold text-lg')
        ui.label('Grant other users permission to create, update, or delete presets in your namespace.').classes('text-sm text-secondary mb-2')

        # Add user button
        ui.button(
            'Add User',
            icon='person_add',
            on_click=self._show_add_permission_dialog
        ).classes('btn mb-4').props('color=primary')

        ui.separator()

        # Permissions list container
        self.permissions_container = ui.element('div').classes('w-full')
        self._render_permissions()

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button('Close', on_click=self._handle_close).classes('btn')

    def _render_permissions(self):
        """Render the list of permissions."""
        if not self.permissions_container:
            return

        self.permissions_container.clear()
        with self.permissions_container:
            if not self.permissions:
                with ui.element('div').classes('text-center py-4'):
                    ui.label('No delegated users yet').classes('text-secondary')
            else:
                for perm in self.permissions:
                    self._render_permission_card(perm)

    def _render_permission_card(self, perm: PresetNamespacePermission):
        """Render a single permission card."""
        with ui.element('div').classes('card mt-2'):
            with ui.element('div').classes('card-body'):
                with ui.row().classes('items-center justify-between w-full'):
                    with ui.column().classes('gap-1'):
                        ui.label(perm.user.get_display_name()).classes('font-bold')
                        perms_list = []
                        if perm.can_create:
                            perms_list.append('Create')
                        if perm.can_update:
                            perms_list.append('Update')
                        if perm.can_delete:
                            perms_list.append('Delete')
                        ui.label(', '.join(perms_list) if perms_list else 'No permissions').classes('text-sm text-secondary')

                    with ui.row().classes('gap-1'):
                        # Edit button
                        async def edit_perm(p=perm):
                            await self._show_edit_permission_dialog(p)

                        ui.button(
                            icon='edit',
                            on_click=edit_perm
                        ).classes('btn btn-sm').props('flat color=primary').tooltip('Edit Permissions')

                        # Remove button
                        async def remove_perm(p=perm):
                            confirm_dialog = ConfirmDialog(
                                title='Remove User',
                                message=f'Remove {p.user.get_display_name()} from this namespace?',
                                on_confirm=lambda: self._remove_permission(p)
                            )
                            await confirm_dialog.show()

                        ui.button(
                            icon='delete',
                            on_click=remove_perm
                        ).classes('btn btn-sm').props('flat color=negative').tooltip('Remove User')

    async def _show_add_permission_dialog(self):
        """Show dialog to add a new user permission."""
        add_dialog = AddPermissionDialog(
            namespace=self.namespace,
            on_save=self._refresh_permissions
        )
        await add_dialog.show()

    async def _show_edit_permission_dialog(self, permission: PresetNamespacePermission):
        """Show dialog to edit an existing permission."""
        edit_dialog = EditPermissionDialog(
            permission=permission,
            on_save=self._refresh_permissions
        )
        await edit_dialog.show()

    async def _remove_permission(self, permission: PresetNamespacePermission):
        """Remove a user permission."""
        try:
            await permission.delete()
            ui.notify('User permission removed successfully', type='positive')
            await self._refresh_permissions()
        except Exception as e:
            logger.error("Failed to remove permission: %s", e, exc_info=True)
            ui.notify(f'Failed to remove permission: {str(e)}', type='negative')

    async def _refresh_permissions(self):
        """Refresh the permissions list."""
        self.permissions = await PresetNamespacePermission.filter(
            namespace_id=self.namespace.id
        ).prefetch_related('user').all()
        self._render_permissions()

    async def _handle_close(self):
        """Handle dialog close."""
        await self.close()
        if self.on_close:
            await self.on_close()
