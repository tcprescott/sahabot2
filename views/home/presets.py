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
                    with ui.element('div').classes('text-center mt-8 mb-8'):
                        ui.icon('code', size='64px').classes('text-secondary')
                        ui.label('No presets found').classes('text-xl text-secondary mt-2')
                        ui.label('Create your first preset to get started! Each user has their own preset namespace.').classes('text-sm text-secondary')
                else:
                    # Presets grid
                    with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4'):
                        for preset in presets:
                            await self._render_preset_card(preset)

            except Exception as e:
                logger.error("Failed to load presets: %s", e, exc_info=True)
                with ui.element('div').classes('p-4 rounded bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'):
                    ui.icon('error').classes('mr-2')
                    ui.label(f'Failed to load presets: {str(e)}').classes('font-bold')
                    ui.label('Please check the server logs for details.').classes('text-sm mt-2')

    async def _render_preset_card(self, preset) -> None:
        """
        Render a single preset card.

        Args:
            preset: Preset to render
        """
        with ui.element('div').classes('card'):
            # Header with randomizer badge
            with ui.element('div').classes('flex justify-between items-center mb-2'):
                ui.label(preset.name).classes('text-lg font-bold')
                randomizer_label = self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer)
                ui.badge(randomizer_label).props('color=primary')

            # Description
            if preset.description:
                ui.label(preset.description).classes('text-sm text-secondary mb-2')

            # Metadata
            with ui.element('div').classes('text-xs text-secondary mb-2'):
                # Scope badge (Global or Namespace)
                with ui.element('div').classes('flex items-center gap-1 mb-1'):
                    if preset.namespace:
                        ui.icon('folder', size='14px')
                        ui.label(f'Namespace: {preset.namespace.display_name}')
                    else:
                        ui.icon('public', size='14px')
                        ui.label('Global Preset').classes('font-bold')

                # Creator
                if preset.user:
                    with ui.element('div').classes('flex items-center gap-1 mb-1'):
                        ui.icon('person', size='14px')
                        ui.label(f'Created by {preset.user.discord_username}')

                # Created date
                with ui.element('div').classes('flex items-center gap-1'):
                    ui.icon('schedule', size='14px')
                    DateTimeLabel.create(preset.created_at)

            # Visibility badge
            visibility_color = 'positive' if preset.is_public else 'warning'
            visibility_text = 'Public' if preset.is_public else 'Private'
            ui.badge(visibility_text).props(f'color={visibility_color}')

            # View YAML button
            async def view_yaml():
                """Display preset YAML content."""
                import yaml

                # Convert settings dict to YAML string
                try:
                    yaml_content = yaml.dump(preset.settings, default_flow_style=False, sort_keys=False)
                except Exception as e:
                    yaml_content = f'Error formatting YAML: {e}'

                # Create a dialog to show the YAML
                with ui.dialog() as yaml_dialog, ui.card().classes('w-full max-w-3xl'):
                    with ui.element('div').classes('flex justify-between items-center mb-4'):
                        ui.label(f'Preset: {preset.name}').classes('text-xl font-bold')
                        ui.button(icon='close', on_click=yaml_dialog.close).props('flat round dense')

                    # YAML content in code block
                    with ui.element('div').classes('mb-4'):
                        ui.code(yaml_content).classes('w-full').style('max-height: 400px; overflow-y: auto;')

                    # Close button
                    with ui.element('div').classes('flex justify-end'):
                        ui.button('Close', on_click=yaml_dialog.close).classes('btn')

                yaml_dialog.open()

            # Edit preset handler
            async def edit_preset():
                """Open edit dialog for this preset."""
                from components.dialogs.organization.preset_editor_dialog import PresetEditorDialog

                dialog = PresetEditorDialog(
                    user=self.user,
                    preset=preset,
                    on_save=self._refresh
                )
                await dialog.show()

            # Delete preset handler
            async def delete_preset():
                """Delete this preset after confirmation."""
                # Confirmation dialog
                with ui.dialog() as confirm_dialog, ui.card():
                    ui.label(f'Delete preset "{preset.name}"?').classes('text-lg font-bold mb-4')
                    ui.label('This action cannot be undone.').classes('text-secondary mb-4')
                    
                    with ui.element('div').classes('flex justify-end gap-2'):
                        ui.button('Cancel', on_click=confirm_dialog.close).classes('btn')
                        
                        async def confirm_delete():
                            try:
                                await self.service.delete_preset(preset.id, self.user)
                                ui.notify(f'Preset "{preset.name}" deleted', type='positive')
                                confirm_dialog.close()
                                await self._refresh()
                            except Exception as e:
                                logger.error("Failed to delete preset %s: %s", preset.id, e, exc_info=True)
                                ui.notify(f'Failed to delete preset: {str(e)}', type='negative')
                        
                        ui.button('Delete', on_click=confirm_delete).classes('btn').props('color=negative')
                
                confirm_dialog.open()

            # Determine if user can edit this preset
            can_edit = preset.user_id == self.user.id or self.user.has_permission('SUPERADMIN')

            ui.separator()
            with ui.element('div').classes('flex justify-between mt-2'):
                # View button on the left
                ui.button('View YAML', icon='code', on_click=view_yaml).classes('btn').props('flat dense')
                
                # Edit and delete buttons on the right (only if user can edit)
                if can_edit:
                    with ui.element('div').classes('flex gap-2'):
                        ui.button('Edit', icon='edit', on_click=edit_preset).classes('btn').props('flat dense color=primary')
                        ui.button('Delete', icon='delete', on_click=delete_preset).classes('btn').props('flat dense color=negative')
