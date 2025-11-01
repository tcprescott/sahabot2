"""
Preset dialogs.

Dialog components for preset management.
"""

import logging
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from models.preset import Preset

logger = logging.getLogger(__name__)


class PresetViewDialog(BaseDialog):
    """Dialog for viewing preset details."""

    def __init__(self, preset: Preset):
        """
        Initialize preset view dialog.

        Args:
            preset: Preset to display
        """
        super().__init__()
        self.preset = preset

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title=f'{self.preset.preset_name}',
            icon='visibility',
            max_width='800px'
        )
        super().show()

    def _render_body(self):
        """Render dialog content."""
        # Metadata
        with ui.element('div').classes('flex flex-col gap-2 mb-4'):
            self.create_info_row('Namespace', self.preset.namespace.name)
            self.create_info_row('Randomizer', self.preset.randomizer.upper())

            if self.preset.description:
                self.create_info_row('Description', self.preset.description)

            self.create_info_row(
                'Last Updated',
                self.preset.updated_at.strftime('%Y-%m-%d %H:%M')
            )

        ui.separator()

        # YAML Content
        self.create_section_title('Content')

        with ui.element('div').classes('bg-gray-100 p-4 rounded mt-2'):
            ui.code(self.preset.content).classes('whitespace-pre-wrap')

        # Actions
        with self.create_actions_row():
            ui.button('Close', on_click=self.close).classes('btn')


class ConfirmDeleteDialog(BaseDialog):
    """Dialog for confirming preset deletion."""

    def __init__(self, message: str, on_confirm):
        """
        Initialize confirm delete dialog.

        Args:
            message: Confirmation message
            on_confirm: Callback when confirmed
        """
        super().__init__()
        self.message = message
        self.on_confirm = on_confirm

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title='Confirm Delete',
            icon='warning',
            max_width='400px'
        )
        super().show()

    def _render_body(self):
        """Render dialog content."""
        ui.label(self.message).classes('text-lg mb-4')

        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button(
                'Delete',
                on_click=lambda: self._confirm()
            ).classes('btn').props('color=negative')

    async def _confirm(self):
        """Handle confirmation."""
        try:
            await self.on_confirm()
            await self.close()
        except Exception as e:
            logger.error("Error in confirmation callback: %s", e, exc_info=True)
            ui.notify(f'Error: {str(e)}', type='negative')
            # Don't close dialog on error
