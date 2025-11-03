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
                    dialog = PresetEditorDialog(is_global=True, on_save=self._refresh)
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
                with ui.element('div').classes('text-center py-8'):
                    ui.icon('code_off', size='4rem').classes('text-gray-400')
                    ui.label('No global presets found').classes('text-lg font-bold mt-2')
                    ui.label('Create a global preset to get started').classes('text-sm text-secondary')
                return

            # Render preset cards
            with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'):
                for preset in presets:
                    await self._render_preset_card(preset)

        except Exception as e:
            logger.error("Error loading global presets: %s", e, exc_info=True)
            ui.label(f'Error loading presets: {str(e)}').classes('text-negative')

    async def _render_preset_card(self, preset) -> None:
        """
        Render a single preset card.

        Args:
            preset: RandomizerPreset to render
        """
        with Card.create():
            # Header with name and randomizer badge
            with ui.element('div').classes('flex items-center justify-between mb-2'):
                ui.label(preset.name).classes('text-lg font-bold')
                ui.badge(
                    self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer),
                    color='primary'
                ).classes('badge')

            # Description (if any)
            if preset.description:
                ui.label(preset.description).classes('text-sm text-secondary mb-2')

            # Metadata
            with ui.element('div').classes('text-xs text-secondary mb-2'):
                ui.label(f'By: {preset.user.discord_username}')
                ui.label(' • ')
                visibility = 'Public' if preset.is_public else 'Private'
                ui.label(f'{visibility}')
                ui.label(' • ')
                with ui.element('span'):
                    ui.label('Updated: ')
                    DateTimeLabel(preset.updated_at)

            # Actions
            with ui.element('div').classes('flex gap-2 mt-4'):
                # View button
                async def view_preset():
                    await self._view_preset(preset)

                ui.button('View', icon='visibility', on_click=view_preset).classes('btn-secondary btn-sm')

                # Edit button (only for owner or superadmin)
                can_edit = await self.service.can_user_edit_preset(preset.id, self.user)
                if can_edit:
                    async def edit_preset():
                        dialog = PresetEditorDialog(preset=preset, on_save=self._refresh)
                        await dialog.show()

                    ui.button('Edit', icon='edit', on_click=edit_preset).classes('btn-secondary btn-sm')

                    # Delete button
                    async def delete_preset():
                        await self._delete_preset(preset)

                    ui.button('Delete', icon='delete', on_click=delete_preset).classes('btn-danger btn-sm')

    async def _view_preset(self, preset) -> None:
        """
        View preset YAML in a dialog.

        Args:
            preset: RandomizerPreset to view
        """
        with ui.dialog() as dialog, ui.card().classes('min-w-96 max-w-2xl'):
            with ui.element('div').classes('flex items-center justify-between mb-4'):
                ui.label(f'Preset: {preset.name}').classes('text-lg font-bold')
                ui.button(icon='close', on_click=dialog.close).props('flat round dense')

            # Metadata
            with ui.element('div').classes('mb-4 text-sm'):
                ui.label(f'Randomizer: {self.RANDOMIZER_LABELS.get(preset.randomizer, preset.randomizer)}')
                if preset.description:
                    ui.label(f'Description: {preset.description}')
                ui.label(f'Created by: {preset.user.discord_username}')
                ui.label(f'Visibility: {"Public" if preset.is_public else "Private"}')

            # YAML content
            yaml_content = yaml.dump(preset.settings, default_flow_style=False, sort_keys=False)

            ui.label('YAML Content:').classes('font-bold mb-2')
            ui.code(yaml_content, language='yaml').classes('w-full')

            # Copy button
            async def copy_yaml():
                await ui.run_javascript(f'navigator.clipboard.writeText({yaml_content!r})')
                ui.notify('YAML copied to clipboard!', type='positive')

            ui.button('Copy YAML', icon='content_copy', on_click=copy_yaml).classes('mt-2')

        await dialog

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
