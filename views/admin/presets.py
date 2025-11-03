"""
Presets View for managing global randomizer presets.

This view allows admins to create, edit, delete, and view global randomizer presets.
Global presets are available to all users and don't belong to any namespace.
"""

from __future__ import annotations
import logging
import yaml
from nicegui import ui
from models import User
from components.card import Card
from components.datetime_label import DateTimeLabel
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs.organization import PresetEditorDialog
from components.dialogs.common.tournament_dialogs import ConfirmDialog
from application.services.randomizer_preset_service import RandomizerPresetService

logger = logging.getLogger(__name__)


class PresetsView:
    """View for managing global randomizer presets (admin only)."""

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

    def __init__(
        self,
        user: User,
        service: RandomizerPresetService
    ):
        """
        Initialize the presets view.

        Args:
            user: Current user
            service: Preset service
        """
        self.user = user
        self.service = service
        self.container = None
        self.filter_randomizer = None
        self.filter_mine_only = False

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
        with Card.create(title='Global Randomizer Presets'):
            # Header with description
            with ui.element('div').classes('mb-4'):
                ui.label('Create and manage global YAML presets for randomizer seed generation.')
                ui.label('Global presets are available to all users and don\'t belong to any namespace.').classes('text-sm text-secondary')

            # Action bar
            with ui.element('div').classes('flex flex-wrap gap-2 mb-4 items-center'):
                # Create button
                async def open_create_dialog():
                    dialog = PresetEditorDialog(user=self.user, is_global=True, on_save=self._refresh)
                    await dialog.show()

                ui.button('Create Global Preset', icon='add', on_click=open_create_dialog).classes('btn').props('color=positive')

                # Filters
                ui.label('Filters:').classes('ml-4 font-bold')

                # Randomizer filter
                randomizer_options = [{'label': 'All Randomizers', 'value': None}]
                randomizer_options.extend([
                    {'label': label, 'value': value}
                    for value, label in self.RANDOMIZER_LABELS.items()
                ])

                async def on_randomizer_change(e):
                    self.filter_randomizer = e.value
                    await self._refresh()

                ui.select(
                    randomizer_options,
                    value=self.filter_randomizer,
                    on_change=on_randomizer_change
                ).classes('w-48')

                # Mine only filter
                async def on_mine_only_change(e):
                    self.filter_mine_only = e.value
                    await self._refresh()

                ui.checkbox('My Presets Only', value=self.filter_mine_only, on_change=on_mine_only_change).classes('ml-2')

            # Presets list
            await self._render_presets_list()

    async def _render_presets_list(self) -> None:
        """Render the list of global presets."""
        try:
            # Fetch global presets only
            presets = await self.service.repository.list_global_presets(
                randomizer=self.filter_randomizer
            )

            # Apply mine_only filter client-side if needed
            if self.filter_mine_only and presets:
                presets = [p for p in presets if p.user_id == self.user.id]

            if not presets:
                # Empty state
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-body text-center py-8'):
                        ui.icon('code_off', size='4rem').classes('text-gray-400')
                        ui.label('No global presets found').classes('text-lg font-bold mt-2')
                        ui.label('Create a global preset to get started').classes('text-sm text-secondary')
                return

            # Render presets table
            with ui.element('div').classes('card'):
                async def render_name_cell(preset):
                    with ui.column().classes('gap-1'):
                        ui.label(preset.name).classes('font-bold')
                        if preset.description:
                            ui.label(preset.description).classes('text-sm text-secondary')

                async def render_randomizer_cell(preset):
                    randomizer_label = self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer)
                    ui.badge(randomizer_label).props('color=primary')

                async def render_creator_cell(preset):
                    ui.label(preset.user.discord_username).classes('text-sm')

                async def render_visibility_cell(preset):
                    visibility_class = 'badge-success' if preset.is_public else 'badge-warning'
                    visibility_text = 'Public' if preset.is_public else 'Private'
                    with ui.element('span').classes(f'badge {visibility_class}'):
                        ui.label(visibility_text)

                async def render_updated_cell(preset):
                    DateTimeLabel.create(preset.updated_at)

                async def render_actions_cell(preset):
                    with ui.row().classes('gap-1'):
                        # View button
                        async def view_preset():
                            await self._view_preset(preset)

                        ui.button(
                            icon='visibility',
                            on_click=view_preset
                        ).classes('btn btn-sm').props('flat').tooltip('View YAML')

                        # Edit button (only for owner or superadmin)
                        can_edit = await self.service.can_user_edit_preset(preset.id, self.user)
                        if can_edit:
                            async def edit_preset():
                                dialog = PresetEditorDialog(user=self.user, preset=preset, on_save=self._refresh)
                                await dialog.show()

                            ui.button(
                                icon='edit',
                                on_click=edit_preset
                            ).classes('btn btn-sm').props('flat').tooltip('Edit')

                            # Delete button
                            async def delete_preset():
                                await self._delete_preset(preset)

                            ui.button(
                                icon='delete',
                                on_click=delete_preset
                            ).classes('btn btn-sm').props('flat color=negative').tooltip('Delete')

                columns = [
                    TableColumn(label='Name', cell_render=render_name_cell),
                    TableColumn(label='Randomizer', cell_render=render_randomizer_cell),
                    TableColumn(label='Creator', cell_render=render_creator_cell),
                    TableColumn(label='Visibility', cell_render=render_visibility_cell),
                    TableColumn(label='Updated', cell_render=render_updated_cell),
                    TableColumn(label='Actions', cell_render=render_actions_cell),
                ]

                table = ResponsiveTable(columns=columns, rows=presets)
                await table.render()

        except Exception as e:
            logger.error("Error loading global presets: %s", e, exc_info=True)
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    ui.label(f'Error loading presets: {str(e)}').classes('text-negative')

    async def _view_preset(self, preset) -> None:
        """
        View preset YAML in a dialog.

        Args:
            preset: RandomizerPreset to view
        """
        with ui.dialog() as dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('visibility').classes('icon-medium')
                            ui.label(f'Preset: {preset.name}').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    # Metadata section
                    with ui.column().classes('gap-2 mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('category', size='sm')
                            ui.label(f'Randomizer: {self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer)}').classes('text-sm')

                        if preset.description:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('description', size='sm')
                                ui.label(f'Description: {preset.description}').classes('text-sm')

                        with ui.row().classes('items-center gap-2'):
                            ui.icon('person', size='sm')
                            ui.label(f'Created by: {preset.user.discord_username}').classes('text-sm')

                        with ui.row().classes('items-center gap-2'):
                            ui.icon('visibility', size='sm')
                            visibility = 'Public' if preset.is_public else 'Private'
                            ui.label(f'Visibility: {visibility}').classes('text-sm')

                    ui.separator()

                    # YAML content
                    ui.label('YAML Content:').classes('font-bold mt-4 mb-2')
                    yaml_content = yaml.dump(preset.settings, default_flow_style=False, sort_keys=False)
                    ui.code(yaml_content, language='yaml').classes('w-full').style('max-height: 400px; overflow-y: auto;')

                    # Action buttons
                    with ui.row().classes('justify-end gap-2 mt-4'):
                        async def copy_yaml():
                            await ui.run_javascript(f'navigator.clipboard.writeText({yaml_content!r})')
                            ui.notify('YAML copied to clipboard!', type='positive')

                        ui.button('Copy YAML', icon='content_copy', on_click=copy_yaml).classes('btn').props('color=primary')
                        ui.button('Close', on_click=dialog.close).classes('btn')

        dialog.open()

    async def _delete_preset(self, preset) -> None:
        """
        Delete a preset with confirmation.

        Args:
            preset: RandomizerPreset to delete
        """
        async def on_confirm():
            try:
                await self.service.delete_preset(preset.id, self.user)
                ui.notify(f'Preset "{preset.name}" deleted', type='positive')
                await self._refresh()
            except Exception as e:
                logger.error("Error deleting preset %s: %s", preset.id, e, exc_info=True)
                ui.notify(f'Error deleting preset: {str(e)}', type='negative')

        dialog = ConfirmDialog(
            title='Delete Preset',
            message=f'Are you sure you want to delete the preset "{preset.name}"? This action cannot be undone.',
            on_confirm=on_confirm
        )
        await dialog.show()
