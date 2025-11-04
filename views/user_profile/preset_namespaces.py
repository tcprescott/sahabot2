"""
Preset Namespaces View for user profile.

Allows users to manage their preset namespaces including
renaming and delegating permissions.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User, PresetNamespace
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from components.dialogs.user_profile import (
    RenameNamespaceDialog,
    ManagePermissionsDialog,
)

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
        dialog = RenameNamespaceDialog(namespace=namespace, on_save=self._refresh)
        await dialog.show()

    async def _show_permissions_dialog(self, namespace: PresetNamespace) -> None:
        """
        Show dialog to manage namespace permissions.

        Args:
            namespace: Namespace to manage permissions for
        """
        dialog = ManagePermissionsDialog(namespace=namespace, on_close=self._refresh)
        await dialog.show()
