"""
Preset list view.

Displays a list of all available presets organized by namespace and randomizer.
"""

import logging
from typing import Optional
from nicegui import ui
from application.services.preset_service import PresetService
from models.user import User

logger = logging.getLogger(__name__)


class PresetListView:
    """View for displaying a list of presets."""

    def __init__(self, service: PresetService, user: Optional[User] = None):
        """
        Initialize preset list view.

        Args:
            service: PresetService instance
            user: Current user (optional)
        """
        self.service = service
        self.user = user

    async def render(self):
        """Render the preset list view."""
        with ui.element('div').classes('page-container'):
            # Header
            with ui.element('div').classes('flex justify-between items-center mb-6'):
                ui.label('Presets').classes('text-2xl font-bold')

                if self.user:
                    with ui.element('div').classes('flex gap-2'):
                        ui.button(
                            'My Presets',
                            on_click=lambda: ui.navigate.to('/presets/my')
                        ).classes('btn')
                        ui.button(
                            'Create Preset',
                            on_click=lambda: ui.navigate.to('/presets/create')
                        ).classes('btn btn-primary')

            # Tabs for different randomizers
            randomizers = ['alttpr', 'smz3', 'sm', 'alttprmystery']

            with ui.tabs().classes('w-full') as tabs:
                for randomizer in randomizers:
                    ui.tab(randomizer.upper(), name=randomizer)

            with ui.tab_panels(tabs, value='alttpr').classes('w-full'):
                for randomizer in randomizers:
                    with ui.tab_panel(randomizer):
                        await self._render_randomizer_presets(randomizer)

    async def _render_randomizer_presets(self, randomizer: str):
        """
        Render presets for a specific randomizer.

        Args:
            randomizer: Randomizer type
        """
        # Get presets organized by namespace
        presets_by_ns = await self.service.list_presets_for_randomizer(
            randomizer,
            include_namespace_names=True
        )

        if not presets_by_ns:
            ui.label(f'No {randomizer.upper()} presets found.').classes('text-center text-gray-500 mt-4')
            return

        # Display by namespace
        for namespace_name, preset_names in sorted(presets_by_ns.items()):
            with ui.expansion(namespace_name, icon='folder').classes('w-full mb-2'):
                with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 p-2'):
                    for preset_name in sorted(preset_names):
                        await self._render_preset_card(namespace_name, randomizer, preset_name)

    async def _render_preset_card(
        self,
        namespace_name: str,
        randomizer: str,
        preset_name: str
    ):
        """
        Render a single preset card.

        Args:
            namespace_name: Namespace name
            randomizer: Randomizer type
            preset_name: Preset name
        """
        with ui.card().classes('preset-card cursor-pointer hover:shadow-lg transition-shadow'):
            # Get preset details
            preset = await self.service.get_preset(namespace_name, preset_name, randomizer)

            with ui.element('div').classes('flex flex-col gap-2'):
                # Preset name
                ui.label(preset_name).classes('font-bold text-lg')

                # Description (if available)
                if preset and preset.description:
                    ui.label(preset.description).classes('text-sm text-gray-600')

                # Actions
                with ui.element('div').classes('flex gap-2 mt-auto'):
                    ui.button(
                        'View',
                        icon='visibility',
                        on_click=lambda p=preset: self._view_preset(p)
                    ).props('flat color=primary size=sm')

                    # Show edit button if user has permission
                    if preset and self.user:
                        can_edit = await self.service.can_edit_namespace(self.user, preset.namespace)
                        if can_edit:
                            ui.button(
                                'Edit',
                                icon='edit',
                                on_click=lambda p=preset: ui.navigate.to(f'/presets/edit/{p.id}')
                            ).props('flat color=secondary size=sm')

    async def _view_preset(self, preset):
        """
        View preset details.

        Args:
            preset: Preset instance
        """
        from components.dialogs.presets import PresetViewDialog

        dialog = PresetViewDialog(preset)
        await dialog.show()
