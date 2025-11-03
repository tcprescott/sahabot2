"""
Presets View for the home page.

This view allows users to browse and view randomizer presets they have access to
across all organizations.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User
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
                    ui.label('Browse randomizer presets from your namespace, global presets, and other accessible namespaces.')
                    ui.label('Global presets are available to everyone. Each user also has their own preset namespace.').classes('text-sm text-secondary')
                
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
                ui.label('Filter:').classes('font-bold')

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

            # Get presets accessible to user (public + user's private)
            try:
                presets = await self.service.list_presets(
                    user=self.user,
                    randomizer=self.filter_randomizer,
                    mine_only=False
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
                                ui.label(preset.user.discord_username).classes('text-sm')
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
        import yaml

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
                                ui.label(f'Created by: {preset.user.discord_username}').classes('text-sm')

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
                            await ui.run_javascript(f'navigator.clipboard.writeText({yaml_content!r})')
                            ui.notify('YAML copied to clipboard!', type='positive')

                        ui.button('Copy YAML', icon='content_copy', on_click=copy_yaml).classes('btn').props('color=primary')
                        ui.button('Close', on_click=yaml_dialog.close).classes('btn')

        yaml_dialog.open()


