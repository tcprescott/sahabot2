"""
Preset Namespaces View for user profile.

Allows users to manage their preset namespaces including
renaming and delegating permissions.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User, PresetNamespace, PresetNamespacePermission
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel

logger = logging.getLogger(__name__)


class PresetNamespacesView:
    """View for managing preset namespaces."""

    def __init__(self, user: User):
        """
        Initialize the preset namespaces view.

        Args:
            user: Current user
        """
        self.user = user
        self.container = None

    async def render(self) -> None:
        """Render the preset namespaces management view."""
        with ui.column().classes('w-full gap-4') as self.container:
            # Page header
            with ui.row().classes('items-center justify-between w-full'):
                with ui.column().classes('gap-1'):
                    ui.label('Preset Namespaces').classes('text-2xl font-bold')
                    ui.label('Manage your preset namespaces and delegate permissions to other users.').classes('text-secondary')

            await self._render_content()

    async def _render_content(self) -> None:
        """Render the main content."""
        # Fetch user's namespaces
        namespaces = await PresetNamespace.filter(user_id=self.user.id).all()

        if not namespaces:
            # Empty state
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body text-center py-8'):
                    ui.icon('folder_open', size='64px').classes('text-secondary')
                    ui.label('No preset namespaces found').classes('text-xl text-secondary mt-2')
                    ui.label('Your personal namespace will be created automatically when you create your first preset.').classes('text-sm text-secondary')
        else:
            # Namespaces table
            with ui.element('div').classes('card'):
                async def render_name_cell(namespace):
                    with ui.column().classes('gap-1'):
                        ui.label(namespace.display_name).classes('font-bold')
                        ui.label(f'ID: {namespace.name}').classes('text-sm text-secondary')

                async def render_description_cell(namespace):
                    if namespace.description:
                        ui.label(namespace.description).classes('text-sm')
                    else:
                        ui.label('—').classes('text-secondary')

                async def render_visibility_cell(namespace):
                    visibility_class = 'badge-success' if namespace.is_public else 'badge-warning'
                    visibility_text = 'Public' if namespace.is_public else 'Private'
                    with ui.element('span').classes(f'badge {visibility_class}'):
                        ui.label(visibility_text)

                async def render_created_cell(namespace):
                    DateTimeLabel.create(namespace.created_at)

                async def render_actions_cell(namespace):
                    with ui.row().classes('gap-1'):
                        # Rename button
                        async def rename_namespace():
                            await self._show_rename_dialog(namespace)

                        ui.button(
                            icon='edit',
                            on_click=rename_namespace
                        ).classes('btn btn-sm').props('flat color=primary').tooltip('Rename Namespace')

                        # Manage permissions button
                        async def manage_permissions():
                            await self._show_permissions_dialog(namespace)

                        ui.button(
                            icon='people',
                            on_click=manage_permissions
                        ).classes('btn btn-sm').props('flat color=primary').tooltip('Manage Permissions')

                columns = [
                    TableColumn(label='Name', cell_render=render_name_cell),
                    TableColumn(label='Description', cell_render=render_description_cell),
                    TableColumn(label='Visibility', cell_render=render_visibility_cell),
                    TableColumn(label='Created', cell_render=render_created_cell),
                    TableColumn(label='Actions', cell_render=render_actions_cell),
                ]

                table = ResponsiveTable(columns=columns, rows=namespaces)
                await table.render()

    async def _refresh(self) -> None:
        """Refresh the content."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _show_rename_dialog(self, namespace: PresetNamespace) -> None:
        """
        Show dialog to rename a namespace.

        Args:
            namespace: Namespace to rename
        """
        with ui.dialog() as rename_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('edit').classes('icon-medium')
                            ui.label('Rename Namespace').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=rename_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    with ui.column().classes('gap-4 w-full'):
                        ui.label(f'Current name: {namespace.display_name}').classes('text-sm text-secondary')

                        # Input fields
                        display_name_input = ui.input(
                            label='Display Name',
                            value=namespace.display_name
                        ).classes('w-full').props('outlined')

                        description_input = ui.textarea(
                            label='Description (optional)',
                            value=namespace.description or ''
                        ).classes('w-full').props('outlined')

                        # Visibility toggle
                        visibility_checkbox = ui.checkbox(
                            'Public (visible to all users)',
                            value=namespace.is_public
                        )

                        # Action buttons
                        with ui.row().classes('justify-end gap-2 mt-4'):
                            ui.button('Cancel', on_click=rename_dialog.close).classes('btn')

                            async def save_changes():
                                try:
                                    namespace.display_name = display_name_input.value
                                    namespace.description = description_input.value or None
                                    namespace.is_public = visibility_checkbox.value
                                    await namespace.save()
                                    ui.notify('Namespace updated successfully', type='positive')
                                    rename_dialog.close()
                                    await self._refresh()
                                except Exception as e:
                                    logger.error("Failed to update namespace %s: %s", namespace.id, e, exc_info=True)
                                    ui.notify(f'Failed to update namespace: {str(e)}', type='negative')

                            ui.button('Save', on_click=save_changes).classes('btn').props('color=positive')

        rename_dialog.open()

    async def _show_permissions_dialog(self, namespace: PresetNamespace) -> None:
        """
        Show dialog to manage namespace permissions.

        Args:
            namespace: Namespace to manage permissions for
        """
        # Fetch existing permissions
        permissions = await PresetNamespacePermission.filter(
            namespace_id=namespace.id
        ).prefetch_related('user').all()

        with ui.dialog() as perm_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('people').classes('icon-medium')
                            ui.label(f'Manage Permissions: {namespace.display_name}').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=perm_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    with ui.column().classes('gap-4 w-full'):
                        ui.label('Delegated Users').classes('font-bold text-lg')
                        ui.label('Grant other users permission to create, update, or delete presets in your namespace.').classes('text-sm text-secondary mb-2')

                        # Add user section
                        async def add_user_permission():
                            await self._show_add_permission_dialog(namespace, perm_dialog)

                        ui.button(
                            'Add User',
                            icon='person_add',
                            on_click=add_user_permission
                        ).classes('btn mb-4').props('color=primary')

                        ui.separator()

                        # Permissions list
                        if not permissions:
                            with ui.element('div').classes('text-center py-4'):
                                ui.label('No delegated users yet').classes('text-secondary')
                        else:
                            for perm in permissions:
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
                                                # Edit permissions
                                                async def edit_perm(p=perm):
                                                    await self._show_edit_permission_dialog(p, perm_dialog)

                                                ui.button(
                                                    icon='edit',
                                                    on_click=edit_perm
                                                ).classes('btn btn-sm').props('flat color=primary').tooltip('Edit Permissions')

                                                # Remove user
                                                async def remove_perm(p=perm):
                                                    from components.dialogs.common.tournament_dialogs import ConfirmDialog
                                                    confirm_dialog = ConfirmDialog(
                                                        title='Remove User',
                                                        message=f'Remove {p.user.get_display_name()} from this namespace?',
                                                        on_confirm=lambda: self._remove_permission(p, perm_dialog)
                                                    )
                                                    await confirm_dialog.show()

                                                ui.button(
                                                    icon='delete',
                                                    on_click=remove_perm
                                                ).classes('btn btn-sm').props('flat color=negative').tooltip('Remove User')

                        # Close button
                        with ui.row().classes('justify-end gap-2 mt-4'):
                            ui.button('Close', on_click=perm_dialog.close).classes('btn')

        perm_dialog.open()

    async def _show_add_permission_dialog(self, namespace: PresetNamespace, parent_dialog) -> None:
        """Show dialog to add a new user permission."""
        with ui.dialog() as add_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('person_add').classes('icon-medium')
                            ui.label('Add User Permission').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=add_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    with ui.column().classes('gap-4 w-full'):
                        ui.label('Enter the Discord username of the user you want to grant permissions to:').classes('text-sm')

                        username_input = ui.input(
                            label='Discord Username',
                            placeholder='username'
                        ).classes('w-full').props('outlined')

                        # Permission checkboxes
                        can_create_cb = ui.checkbox('Can Create Presets', value=True)
                        can_update_cb = ui.checkbox('Can Update Presets', value=True)
                        can_delete_cb = ui.checkbox('Can Delete Presets', value=False)

                        # Action buttons
                        with ui.row().classes('justify-end gap-2 mt-4'):
                            ui.button('Cancel', on_click=add_dialog.close).classes('btn')

                            async def save_permission():
                                try:
                                    # Find user by username
                                    target_user = await User.filter(
                                        discord_username__iexact=username_input.value
                                    ).first()

                                    if not target_user:
                                        ui.notify('User not found', type='negative')
                                        return

                                    # Check if permission already exists
                                    existing = await PresetNamespacePermission.filter(
                                        namespace_id=namespace.id,
                                        user_id=target_user.id
                                    ).first()

                                    if existing:
                                        ui.notify('User already has permissions in this namespace', type='warning')
                                        return

                                    # Create permission
                                    await PresetNamespacePermission.create(
                                        namespace=namespace,
                                        user=target_user,
                                        can_create=can_create_cb.value,
                                        can_update=can_update_cb.value,
                                        can_delete=can_delete_cb.value
                                    )

                                    ui.notify('User permission added successfully', type='positive')
                                    add_dialog.close()
                                    parent_dialog.close()
                                    await self._show_permissions_dialog(namespace)

                                except Exception as e:
                                    logger.error("Failed to add permission: %s", e, exc_info=True)
                                    ui.notify(f'Failed to add permission: {str(e)}', type='negative')

                            ui.button('Add', on_click=save_permission).classes('btn').props('color=positive')

        add_dialog.open()

    async def _show_edit_permission_dialog(self, permission: PresetNamespacePermission, parent_dialog) -> None:
        """Show dialog to edit user permissions."""
        await permission.fetch_related('namespace')

        with ui.dialog() as edit_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('edit').classes('icon-medium')
                            ui.label(f'Edit Permissions: {permission.user.get_display_name()}').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=edit_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    with ui.column().classes('gap-4 w-full'):
                        # Permission checkboxes
                        can_create_cb = ui.checkbox('Can Create Presets', value=permission.can_create)
                        can_update_cb = ui.checkbox('Can Update Presets', value=permission.can_update)
                        can_delete_cb = ui.checkbox('Can Delete Presets', value=permission.can_delete)

                        # Action buttons
                        with ui.row().classes('justify-end gap-2 mt-4'):
                            ui.button('Cancel', on_click=edit_dialog.close).classes('btn')

                            async def save_changes():
                                try:
                                    permission.can_create = can_create_cb.value
                                    permission.can_update = can_update_cb.value
                                    permission.can_delete = can_delete_cb.value
                                    await permission.save()

                                    ui.notify('Permissions updated successfully', type='positive')
                                    edit_dialog.close()
                                    parent_dialog.close()
                                    await self._show_permissions_dialog(permission.namespace)

                                except Exception as e:
                                    logger.error("Failed to update permission: %s", e, exc_info=True)
                                    ui.notify(f'Failed to update permission: {str(e)}', type='negative')

                            ui.button('Save', on_click=save_changes).classes('btn').props('color=positive')

        edit_dialog.open()

    async def _remove_permission(self, permission: PresetNamespacePermission, parent_dialog) -> None:
        """Remove a user permission."""
        try:
            await permission.fetch_related('namespace')
            namespace = permission.namespace
            await permission.delete()
            ui.notify('User permission removed successfully', type='positive')
            parent_dialog.close()
            await self._show_permissions_dialog(namespace)
        except Exception as e:
            logger.error("Failed to remove permission: %s", e, exc_info=True)
            ui.notify(f'Failed to remove permission: {str(e)}', type='negative')
