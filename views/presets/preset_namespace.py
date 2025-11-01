"""
Preset namespace view.

Displays presets within a specific namespace.
"""

import logging
from typing import Optional
from nicegui import ui
from application.services.preset_service import PresetService
from models.preset import PresetNamespace
from models.user import User

logger = logging.getLogger(__name__)


class PresetNamespaceView:
    """View for displaying presets in a namespace."""

    def __init__(
        self,
        service: PresetService,
        namespace: PresetNamespace,
        user: Optional[User] = None
    ):
        """
        Initialize namespace view.

        Args:
            service: PresetService instance
            namespace: PresetNamespace to display
            user: Current user (optional)
        """
        self.service = service
        self.namespace = namespace
        self.user = user

    async def render(self):
        """Render the namespace view."""
        with ui.element('div').classes('page-container'):
            # Header
            with ui.element('div').classes('flex justify-between items-center mb-6'):
                with ui.element('div'):
                    ui.label(f'Namespace: {self.namespace.name}').classes('text-2xl font-bold')
                    if self.namespace.description:
                        ui.label(self.namespace.description).classes('text-gray-600')

                # Actions for owners
                if self.user and self.service.is_namespace_owner(self.user, self.namespace):
                    ui.button(
                        'Create Preset',
                        icon='add',
                        on_click=lambda: ui.navigate.to('/presets/create')
                    ).classes('btn btn-primary')

            # Get presets in this namespace
            presets = await self.service.list_presets(
                namespace_name=self.namespace.name,
                user=self.user
            )

            if not presets:
                ui.label('No presets in this namespace yet.').classes('text-center text-gray-500 mt-8')
                return

            # Group by randomizer
            presets_by_randomizer = {}
            for preset in presets:
                if preset.randomizer not in presets_by_randomizer:
                    presets_by_randomizer[preset.randomizer] = []
                presets_by_randomizer[preset.randomizer].append(preset)

            # Display grouped presets
            for randomizer, randomizer_presets in sorted(presets_by_randomizer.items()):
                with ui.expansion(randomizer.upper(), icon='category').classes('w-full mb-4'):
                    with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4'):
                        for preset in sorted(randomizer_presets, key=lambda p: p.preset_name):
                            await self._render_preset_card(preset)

    async def _render_preset_card(self, preset):
        """
        Render a preset card.

        Args:
            preset: Preset instance
        """
        can_edit = False
        if self.user:
            can_edit = await self.service.can_edit_namespace(self.user, preset.namespace)

        with ui.card().classes('preset-card'):
            with ui.element('div').classes('flex flex-col gap-2'):
                ui.label(preset.preset_name).classes('font-bold text-lg')

                if preset.description:
                    ui.label(preset.description).classes('text-sm text-gray-600')

                # Metadata
                with ui.element('div').classes('flex gap-2 text-xs text-gray-500 mt-2'):
                    ui.label(f'Updated: {preset.updated_at.strftime("%Y-%m-%d")}')

                # Actions
                with ui.element('div').classes('flex gap-2 mt-auto'):
                    ui.button(
                        'View',
                        icon='visibility',
                        on_click=lambda p=preset: self._view_preset(p)
                    ).props('flat color=primary size=sm')

                    if can_edit:
                        ui.button(
                            'Edit',
                            icon='edit',
                            on_click=lambda p=preset: ui.navigate.to(f'/presets/edit/{p.id}')
                        ).props('flat color=secondary size=sm')

                        ui.button(
                            'Delete',
                            icon='delete',
                            on_click=lambda p=preset: self._delete_preset(p)
                        ).props('flat color=negative size=sm')

    async def _view_preset(self, preset):
        """View preset in dialog."""
        from components.dialogs.presets import PresetViewDialog
        dialog = PresetViewDialog(preset)
        await dialog.show()

    async def _delete_preset(self, preset):
        """Delete a preset with confirmation."""
        from components.dialogs.presets import ConfirmDeleteDialog

        async def on_confirm():
            success = await self.service.delete_preset(preset, self.user)
            if success:
                ui.notify(f'Deleted preset {preset.preset_name}', type='positive')
                ui.navigate.reload()
            else:
                ui.notify('Failed to delete preset', type='negative')

        dialog = ConfirmDeleteDialog(
            f'Delete preset "{preset.preset_name}"?',
            on_confirm
        )
        await dialog.show()
