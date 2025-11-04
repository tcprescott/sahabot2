"""
Presets View for the home page.

This view allows users to browse and view randomizer presets they have access to
across all organizations.
"""

from __future__ import annotations
import logging
import yaml
from nicegui import ui
from models import User
from models.user import Permission
from components.card import Card
from components.datetime_label import DateTimeLabel
from components.data_table import ResponsiveTable, TableColumn
from application.services.randomizer_preset_service import RandomizerPresetService

logger = logging.getLogger(__name__)


class PresetsView:
    """View for browsing accessible randomizer presets."""

    RANDOMIZER_LABELS = {
        'alttpr': 'ALTTPR',
        'sm': 'Super Metroid',
        'smz3': 'SMZ3 Combo',
        'ootr': 'OoTR',
        'aosr': 'Aria of Sorrow',
        'z1r': 'Zelda 1',
        'ffr': 'FF Randomizer',
        'smb3r': 'SMB3 Randomizer',
        'ctjets': 'CT: Jets of Time',
        'bingosync': 'Bingosync',
    }

    def __init__(self, user: User):
        """
        Initialize the presets view.

        Args:
            user: Current user
        """
        self.user = user
        self.service = RandomizerPresetService()
        self.container = None
        self.filter_randomizer = None
        self.filter_mine_only = True  # Default to showing only user's namespace
        self.filter_include_global = True  # Always include global presets

    async def render(self) -> None:
        """Render the presets view."""
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
        with Card.create(title='Randomizer Presets'):
            # Header with description and create button
            with ui.element('div').classes('flex justify-between items-start mb-4'):
                with ui.element('div'):
                    ui.label('Browse randomizer presets from your namespace, global presets, and other public namespaces.')
                    ui.label('Use filters below to show only your namespace or explore all public presets.').classes('text-sm text-secondary')
                
                # Create preset button
                async def create_preset():
                    """Open dialog to create a new preset."""
                    from components.dialogs.organization.preset_editor_dialog import PresetEditorDialog
                    
                    dialog = PresetEditorDialog(
                        user=self.user,
                        on_save=self._refresh
                    )
                    await dialog.show()

                ui.button('Create Preset', icon='add', on_click=create_preset).classes('btn').props('color=positive')

            # Filter bar
            with ui.element('div').classes('flex flex-wrap gap-2 mb-4 items-center'):
                ui.label('Filters:').classes('font-bold')

                # Randomizer filter
                randomizer_options = {'All Randomizers': None}
                randomizer_options.update(self.RANDOMIZER_LABELS)

                async def on_randomizer_change(e):
                    self.filter_randomizer = e.value
                    await self._refresh()

                ui.select(
                    label='Randomizer',
                    options=randomizer_options,
                    value=self.filter_randomizer,
                    on_change=on_randomizer_change,
                    with_input=True
                ).classes('w-48').props('outlined dense')

                # Scope filter (Mine Only vs All Public)
                scope_options = {
                    'mine': 'My Namespace Only',
                    'all': 'All Public Presets'
                }

                async def on_scope_change(e):
                    self.filter_mine_only = (e.value == 'mine')
                    await self._refresh()

                ui.select(
                    label='Scope',
                    options=scope_options,
                    value='mine' if self.filter_mine_only else 'all',
                    on_change=on_scope_change
                ).classes('w-48').props('outlined dense')

                # Include global presets checkbox
                async def on_include_global_change(e):
                    self.filter_include_global = e.value
                    await self._refresh()

                ui.checkbox(
                    'Include Global Presets',
                    value=self.filter_include_global,
                    on_change=on_include_global_change
                )

            # Get presets accessible to user
            try:
                presets = await self.service.list_presets(
                    user=self.user,
                    randomizer=self.filter_randomizer,
                    mine_only=self.filter_mine_only,
                    include_global=self.filter_include_global
                )

                if not presets:
                    # Empty state
                    with ui.element('div').classes('card'):
                        with ui.element('div').classes('card-body text-center py-8'):
                            ui.icon('code', size='64px').classes('text-secondary')
                            ui.label('No presets found').classes('text-xl text-secondary mt-2')
                            ui.label('Create your first preset to get started! Each user has their own preset namespace.').classes('text-sm text-secondary')
                else:
                    # Presets table
                    with ui.element('div').classes('card'):
                        async def render_name_cell(preset):
                            with ui.column().classes('gap-1'):
                                ui.label(preset.name).classes('font-bold')
                                if preset.description:
                                    ui.label(preset.description).classes('text-sm text-secondary')

                        async def render_randomizer_cell(preset):
                            randomizer_label = self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer)
                            ui.badge(randomizer_label).props('color=primary')

                        async def render_scope_cell(preset):
                            if preset.namespace:
                                with ui.row().classes('items-center gap-1'):
                                    ui.icon('folder', size='14px')
                                    ui.label(preset.namespace.display_name).classes('text-sm')
                            else:
                                with ui.row().classes('items-center gap-1'):
                                    ui.icon('public', size='14px')
                                    ui.label('Global').classes('text-sm font-bold')

                        async def render_creator_cell(preset):
                            if preset.user:
                                ui.label(preset.user.get_display_name()).classes('text-sm')
                            else:
                                ui.label('—').classes('text-secondary')

                        async def render_visibility_cell(preset):
                            visibility_class = 'badge-success' if preset.is_public else 'badge-warning'
                            visibility_text = 'Public' if preset.is_public else 'Private'
                            with ui.element('span').classes(f'badge {visibility_class}'):
                                ui.label(visibility_text)

                        async def render_created_cell(preset):
                            DateTimeLabel.create(preset.created_at)

                        async def render_actions_cell(preset):
                            with ui.row().classes('gap-1'):
                                # View button
                                async def view_yaml():
                                    await self._view_preset_yaml(preset)

                                ui.button(
                                    icon='visibility',
                                    on_click=view_yaml
                                ).classes('btn btn-sm').props('flat').tooltip('View YAML')

                                # Edit and delete buttons (only if user owns preset or is SUPERADMIN)
                                can_edit = (preset.user_id == self.user.id or
                                           self.user.has_permission(Permission.SUPERADMIN))

                                if can_edit:
                                    async def edit_preset():
                                        from components.dialogs.organization.preset_editor_dialog import PresetEditorDialog
                                        dialog = PresetEditorDialog(
                                            user=self.user,
                                            preset=preset,
                                            on_save=self._refresh
                                        )
                                        await dialog.show()

                                    ui.button(
                                        icon='edit',
                                        on_click=edit_preset
                                    ).classes('btn btn-sm').props('flat color=primary').tooltip('Edit Preset')

                                    # Delete button
                                    async def delete_preset():
                                        from components.dialogs.common.tournament_dialogs import ConfirmDialog
                                        dialog = ConfirmDialog(
                                            title='Delete Preset',
                                            message=f'Are you sure you want to delete "{preset.name}"? This action cannot be undone.',
                                            on_confirm=lambda: self._delete_preset(preset.id)
                                        )
                                        await dialog.show()

                                    ui.button(
                                        icon='delete',
                                        on_click=delete_preset
                                    ).classes('btn btn-sm').props('flat color=negative').tooltip('Delete Preset')

                        columns = [
                            TableColumn(label='Name', cell_render=render_name_cell),
                            TableColumn(label='Randomizer', cell_render=render_randomizer_cell),
                            TableColumn(label='Scope', cell_render=render_scope_cell),
                            TableColumn(label='Creator', cell_render=render_creator_cell),
                            TableColumn(label='Visibility', cell_render=render_visibility_cell),
                            TableColumn(label='Created', cell_render=render_created_cell),
                            TableColumn(label='Actions', cell_render=render_actions_cell),
                        ]

                        table = ResponsiveTable(columns=columns, rows=presets)
                        await table.render()

            except Exception as e:
                logger.error("Failed to load presets: %s", e, exc_info=True)
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-body'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('error').classes('text-negative')
                            with ui.column():
                                ui.label(f'Failed to load presets: {str(e)}').classes('font-bold text-negative')
                                ui.label('Please check the server logs for details.').classes('text-sm text-secondary')

    async def _view_preset_yaml(self, preset) -> None:
        """
        Display preset YAML content in a dialog.

        Args:
            preset: Preset to view
        """
        # Convert settings dict to YAML string
        try:
            yaml_content = yaml.dump(preset.settings, default_flow_style=False, sort_keys=False)
        except Exception as e:
            yaml_content = f'Error formatting YAML: {e}'

        # Create a dialog to show the YAML
        with ui.dialog() as yaml_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('visibility').classes('icon-medium')
                            ui.label(f'Preset: {preset.name}').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=yaml_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    # Metadata section
                    with ui.column().classes('gap-2 mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('category', size='sm')
                            randomizer_label = self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer)
                            ui.label(f'Randomizer: {randomizer_label}').classes('text-sm')

                        if preset.description:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('description', size='sm')
                                ui.label(f'Description: {preset.description}').classes('text-sm')

                        # Scope
                        with ui.row().classes('items-center gap-2'):
                            if preset.namespace:
                                ui.icon('folder', size='sm')
                                ui.label(f'Namespace: {preset.namespace.display_name}').classes('text-sm')
                            else:
                                ui.icon('public', size='sm')
                                ui.label('Scope: Global').classes('text-sm font-bold')

                        # Creator
                        if preset.user:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('person', size='sm')
                                ui.label(f'Created by: {preset.user.get_display_name()}').classes('text-sm')

                        # Visibility
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('visibility', size='sm')
                            visibility = 'Public' if preset.is_public else 'Private'
                            ui.label(f'Visibility: {visibility}').classes('text-sm')

                    ui.separator()

                    # YAML content
                    ui.label('YAML Content:').classes('font-bold mt-4 mb-2')
                    ui.code(yaml_content, language='yaml').classes('w-full').style('max-height: 400px; overflow-y: auto;')

                    # Action buttons
                    with ui.row().classes('justify-end gap-2 mt-4'):
                        async def copy_yaml():
                            success = await ui.run_javascript(
                                f'return window.ClipboardUtils.copy({yaml_content!r});'
                            )
                            if success:
                                ui.notify('YAML copied to clipboard!', type='positive')
                            else:
                                ui.notify('Failed to copy YAML', type='negative')

                        ui.button('Copy YAML', icon='content_copy', on_click=copy_yaml).classes('btn').props('color=primary')
                        ui.button('Close', on_click=yaml_dialog.close).classes('btn')

        yaml_dialog.open()

    async def _delete_preset(self, preset_id: int) -> None:
        """
        Delete a preset.

        Args:
            preset_id: Preset ID to delete
        """
        try:
            success = await self.service.delete_preset(preset_id, self.user)
            if success:
                ui.notify('Preset deleted successfully', type='positive')
                await self._refresh()
            else:
                ui.notify('Failed to delete preset', type='negative')
        except PermissionError:
            ui.notify('Not authorized to delete this preset', type='negative')
        except Exception as e:
            logger.error("Failed to delete preset %s: %s", preset_id, e, exc_info=True)
            ui.notify(f'Error deleting preset: {str(e)}', type='negative')

