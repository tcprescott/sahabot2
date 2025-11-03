"""
Preset Namespaces View for admin panel.

This view allows admins to view, create, edit, and delete preset namespaces.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User, PresetNamespace
from components.card import Card
from components.datetime_label import DateTimeLabel
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
        # Table header
        with ui.element('div').classes('grid grid-cols-5 gap-4 p-3 bg-gray-100 dark:bg-gray-800 font-bold border-b'):
            ui.label('Name')
            ui.label('Display Name')
            ui.label('Owner')
            ui.label('Visibility')
            ui.label('Actions')

        # Table rows
        for namespace in namespaces:
            with ui.element('div').classes('grid grid-cols-5 gap-4 p-3 border-b hover:bg-gray-50 dark:hover:bg-gray-800'):
                # Name
                with ui.element('div'):
                    ui.label(namespace.name).classes('font-mono')
                    if namespace.description:
                        ui.label(namespace.description).classes('text-xs text-secondary')

                # Display name
                ui.label(namespace.display_name)

                # Owner
                with ui.element('div'):
                    if namespace.user:
                        ui.badge(f'User: {namespace.user.get_display_name()}').props('color=primary')
                    elif namespace.organization:
                        ui.badge(f'Org: {namespace.organization.name}').props('color=secondary')
                    else:
                        ui.badge('System').props('color=warning')

                # Visibility
                visibility_color = 'positive' if namespace.is_public else 'warning'
                visibility_text = 'Public' if namespace.is_public else 'Private'
                ui.badge(visibility_text).props(f'color={visibility_color}')

                # Actions
                with ui.element('div').classes('flex gap-2'):
                    # View button
                    async def view_namespace(ns=namespace):
                        await self._view_namespace(ns)

                    ui.button('View', icon='visibility', on_click=view_namespace).classes('btn').props('flat dense')

                    # Delete button (only for non-user namespaces or if no presets)
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

        with ui.dialog() as view_dialog, ui.card().classes('w-full max-w-2xl'):
            with ui.element('div').classes('flex justify-between items-center mb-4'):
                ui.label(f'Namespace: {namespace.display_name}').classes('text-xl font-bold')
                ui.button(icon='close', on_click=view_dialog.close).props('flat round dense')

            # Details
            with ui.element('div').classes('space-y-3'):
                # Name
                with ui.element('div'):
                    ui.label('Name:').classes('font-bold')
                    ui.label(namespace.name).classes('font-mono')

                # Display Name
                with ui.element('div'):
                    ui.label('Display Name:').classes('font-bold')
                    ui.label(namespace.display_name)

                # Description
                if namespace.description:
                    with ui.element('div'):
                        ui.label('Description:').classes('font-bold')
                        ui.label(namespace.description)

                # Owner
                with ui.element('div'):
                    ui.label('Owner:').classes('font-bold')
                    if namespace.user:
                        ui.label(f'User: {namespace.user.get_display_name()}')
                    elif namespace.organization:
                        ui.label(f'Organization: {namespace.organization.name}')
                    else:
                        ui.label('System')

                # Visibility
                with ui.element('div'):
                    ui.label('Visibility:').classes('font-bold')
                    ui.label('Public' if namespace.is_public else 'Private')

                # Preset count
                with ui.element('div'):
                    ui.label('Presets:').classes('font-bold')
                    ui.label(f'{len(namespace.presets)} preset(s)')

                # Timestamps
                with ui.element('div'):
                    ui.label('Created:').classes('font-bold')
                    DateTimeLabel.create(namespace.created_at)

                with ui.element('div'):
                    ui.label('Updated:').classes('font-bold')
                    DateTimeLabel.create(namespace.updated_at)

            # Close button
            ui.separator().classes('my-4')
            with ui.element('div').classes('flex justify-end'):
                ui.button('Close', on_click=view_dialog.close).classes('btn')

        view_dialog.open()

    async def _delete_namespace(self, namespace: PresetNamespace) -> None:
        """
        Delete a namespace after confirmation.

        Args:
            namespace: Namespace to delete
        """
        # Fetch preset count
        await namespace.fetch_related('presets')
        preset_count = len(namespace.presets)

        # Confirmation dialog
        with ui.dialog() as confirm_dialog, ui.card():
            ui.label(f'Delete namespace "{namespace.display_name}"?').classes('text-lg font-bold mb-4')
            
            if preset_count > 0:
                ui.label(f'Warning: This namespace has {preset_count} preset(s).').classes('text-red-600 font-bold mb-2')
                ui.label('Deleting this namespace will also delete all its presets.').classes('text-secondary mb-4')
            else:
                ui.label('This action cannot be undone.').classes('text-secondary mb-4')

            with ui.element('div').classes('flex justify-end gap-2'):
                ui.button('Cancel', on_click=confirm_dialog.close).classes('btn')

                async def confirm_delete():
                    try:
                        from application.repositories.preset_namespace_repository import PresetNamespaceRepository
                        repo = PresetNamespaceRepository()
                        await repo.delete(namespace.id)
                        ui.notify(f'Namespace "{namespace.display_name}" deleted', type='positive')
                        confirm_dialog.close()
                        await self._refresh()
                    except Exception as e:
                        logger.error("Failed to delete namespace %s: %s", namespace.id, e, exc_info=True)
                        ui.notify(f'Failed to delete namespace: {str(e)}', type='negative')

                ui.button('Delete', on_click=confirm_delete).classes('btn').props('color=negative')

        confirm_dialog.open()
