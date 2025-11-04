"""
Preset Namespaces View for admin panel.

This view allows admins to view, create, edit, and delete preset namespaces.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User, PresetNamespace
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs import ViewNamespaceDialog, ConfirmDialog
from application.services.preset_namespace_service import PresetNamespaceService

logger = logging.getLogger(__name__)


class PresetNamespacesView:
    """View for managing preset namespaces (admin only)."""

    def __init__(self, user: User):
        """
        Initialize the preset namespaces view.

        Args:
            user: Current user (must be admin)
        """
        self.user = user
        self.service = PresetNamespaceService()
        self.container = None

    async def render(self) -> None:
        """Render the preset namespaces view."""
        self.container = ui.column().classes('w-full')
        with self.container:
            await self._render_content()

    async def _refresh(self) -> None:
        """Refresh the view."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _render_content(self) -> None:
        """Render the view content."""
        with Card.create(title='Preset Namespaces'):
            # Header with description
            with ui.element('div').classes('mb-4'):
                ui.label('Manage preset namespaces for organizing randomizer presets.')
                ui.label('Namespaces can be owned by users or organizations.').classes('text-sm text-secondary')

            # Load namespaces
            try:
                # Get all namespaces (admin view)
                from application.repositories.preset_namespace_repository import PresetNamespaceRepository
                repo = PresetNamespaceRepository()
                namespaces = await repo.list_all()

                if not namespaces:
                    # Empty state
                    with ui.element('div').classes('text-center mt-8 mb-8'):
                        ui.icon('folder', size='64px').classes('text-secondary')
                        ui.label('No namespaces found').classes('text-xl text-secondary mt-2')
                        ui.label('Namespaces are created automatically when users create their first preset.').classes('text-sm text-secondary')
                else:
                    # Namespaces table
                    with ui.element('div').classes('mt-4'):
                        await self._render_namespaces_table(namespaces)

            except Exception as e:
                logger.error("Failed to load namespaces: %s", e, exc_info=True)
                with ui.element('div').classes('p-4 rounded bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'):
                    ui.icon('error').classes('mr-2')
                    ui.label(f'Failed to load namespaces: {str(e)}').classes('font-bold')

    async def _render_namespaces_table(self, namespaces: list[PresetNamespace]) -> None:
        """
        Render namespaces in a table.

        Args:
            namespaces: List of namespaces to display
        """
        # Define table columns
        columns = [
            TableColumn(
                label='Name',
                cell_render=lambda ns: self._render_name_cell(ns)
            ),
            TableColumn(
                label='Display Name',
                key='display_name'
            ),
            TableColumn(
                label='Owner',
                cell_render=lambda ns: self._render_owner_cell(ns)
            ),
            TableColumn(
                label='Visibility',
                cell_render=lambda ns: self._render_visibility_cell(ns)
            ),
            TableColumn(
                label='Actions',
                cell_render=lambda ns: self._render_actions_cell(ns)
            ),
        ]

        # Render table
        table = ResponsiveTable(columns=columns, rows=namespaces)
        await table.render()

    def _render_name_cell(self, namespace: PresetNamespace) -> None:
        """Render the name cell."""
        with ui.column().classes('gap-1'):
            ui.label(namespace.name).classes('font-mono')
            if namespace.description:
                ui.label(namespace.description).classes('text-xs text-secondary')

    def _render_owner_cell(self, namespace: PresetNamespace) -> None:
        """Render the owner cell."""
        if namespace.user:
            ui.badge(f'User: {namespace.user.get_display_name()}').props('color=primary')
        elif namespace.organization:
            ui.badge(f'Org: {namespace.organization.name}').props('color=secondary')
        else:
            ui.badge('System').props('color=warning')

    def _render_visibility_cell(self, namespace: PresetNamespace) -> None:
        """Render the visibility cell."""
        visibility_color = 'positive' if namespace.is_public else 'warning'
        visibility_text = 'Public' if namespace.is_public else 'Private'
        ui.badge(visibility_text).props(f'color={visibility_color}')

    def _render_actions_cell(self, namespace: PresetNamespace) -> None:
        """Render the actions cell."""
        with ui.row().classes('gap-2'):
            # View button
            async def view_namespace(ns=namespace):
                await self._view_namespace(ns)

            ui.button('View', icon='visibility', on_click=view_namespace).classes('btn').props('flat dense')

            # Delete button
            async def delete_namespace(ns=namespace):
                await self._delete_namespace(ns)

            ui.button('Delete', icon='delete', on_click=delete_namespace).classes('btn').props('flat dense color=negative')

    async def _view_namespace(self, namespace: PresetNamespace) -> None:
        """
        Display namespace details in a dialog.

        Args:
            namespace: Namespace to view
        """
        # Fetch related data
        await namespace.fetch_related('user', 'organization', 'presets')

        # Show dialog
        dialog = ViewNamespaceDialog(namespace=namespace)
        await dialog.show()

    async def _delete_namespace(self, namespace: PresetNamespace) -> None:
        """
        Delete a namespace after confirmation.

        Args:
            namespace: Namespace to delete
        """
        # Fetch preset count
        await namespace.fetch_related('presets')
        preset_count = len(namespace.presets)

        # Build confirmation message
        message = f'Are you sure you want to delete namespace "{namespace.display_name}"?'
        if preset_count > 0:
            message += f'\n\nWarning: This namespace has {preset_count} preset(s). Deleting this namespace will also delete all its presets.'
        else:
            message += '\n\nThis action cannot be undone.'

        async def confirm_delete():
            """Delete the namespace."""
            try:
                from application.repositories.preset_namespace_repository import PresetNamespaceRepository
                repo = PresetNamespaceRepository()
                await repo.delete(namespace.id)
                ui.notify(f'Namespace "{namespace.display_name}" deleted', type='positive')
                await self._refresh()
            except Exception as e:
                logger.error("Failed to delete namespace %s: %s", namespace.id, e, exc_info=True)
                ui.notify(f'Failed to delete namespace: {str(e)}', type='negative')

        # Show confirmation dialog
        dialog = ConfirmDialog(
            title='Delete Namespace',
            message=message,
            on_confirm=confirm_delete
        )
        await dialog.show()
