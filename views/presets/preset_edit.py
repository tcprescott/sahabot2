"""
Preset edit view.

Provides a YAML editor for creating and editing presets.
"""

import logging
from typing import Optional
from nicegui import ui
from application.services.preset_service import PresetService
from models.preset import Preset
from models.user import User

logger = logging.getLogger(__name__)


class PresetEditView:
    """View for editing presets with YAML editor."""

    def __init__(
        self,
        service: PresetService,
        preset: Preset,
        user: User,
        is_create: bool = False
    ):
        """
        Initialize preset edit view.

        Args:
            service: PresetService instance
            preset: Preset to edit (or empty for creation)
            user: Current user
            is_create: True if creating new preset
        """
        self.service = service
        self.preset = preset
        self.user = user
        self.is_create = is_create

    async def render(self):
        """Render the preset editor."""
        with ui.element('div').classes('page-container'):
            # Header
            title = 'Create Preset' if self.is_create else f'Edit: {self.preset.preset_name}'
            ui.label(title).classes('text-2xl font-bold mb-6')

            # Form
            with ui.card().classes('w-full'):
                with ui.element('div').classes('flex flex-col gap-4 p-4'):
                    # Namespace (if creating)
                    if self.is_create:
                        # Get user's namespaces
                        namespaces = await self.service.list_namespaces(user=self.user)
                        editable_ns = [
                            ns for ns in namespaces
                            if await self.service.can_edit_namespace(self.user, ns)
                        ]

                        namespace_options = {ns.name: ns.name for ns in editable_ns}
                        namespace_select = ui.select(
                            label='Namespace',
                            options=namespace_options,
                            value=self.preset.namespace.name if self.preset.namespace else None
                        ).classes('w-full')

                    # Preset name
                    preset_name_input = ui.input(
                        label='Preset Name',
                        placeholder='my-preset',
                        value=self.preset.preset_name if not self.is_create else ''
                    ).classes('w-full')
                    preset_name_input.props('clearable')

                    # Randomizer selection
                    randomizer_options = {
                        'alttpr': 'ALTTPR',
                        'smz3': 'SMZ3',
                        'sm': 'Super Metroid',
                        'alttprmystery': 'ALTTPR Mystery'
                    }
                    randomizer_select = ui.select(
                        label='Randomizer',
                        options=randomizer_options,
                        value=self.preset.randomizer if self.preset.randomizer else 'alttpr'
                    ).classes('w-full')

                    # Description
                    description_input = ui.textarea(
                        label='Description (optional)',
                        placeholder='Brief description of this preset...',
                        value=self.preset.description if self.preset.description else ''
                    ).classes('w-full')

                    # YAML Editor
                    ui.label('Preset Content (YAML)').classes('font-bold mt-4')

                    content_editor = ui.textarea(
                        label='',
                        placeholder='# Enter YAML content here\ngoal_name: example\nsettings:\n  preset: standard',
                        value=self.preset.content if self.preset.content else ''
                    ).classes('w-full font-mono').props('rows=20')

                    # Validation message area
                    validation_msg = ui.label('').classes('text-sm')

                    # Action buttons
                    with ui.element('div').classes('flex justify-between mt-4'):
                        ui.button(
                            'Cancel',
                            on_click=lambda: ui.navigate.back()
                        ).classes('btn')

                        with ui.element('div').classes('flex gap-2'):
                            ui.button(
                                'Validate YAML',
                                icon='check_circle',
                                on_click=lambda: self._validate_yaml(
                                    content_editor.value,
                                    validation_msg
                                )
                            ).classes('btn')

                            ui.button(
                                'Save' if not self.is_create else 'Create',
                                icon='save',
                                on_click=lambda: self._save_preset(
                                    namespace_select.value if self.is_create else self.preset.namespace.name,
                                    preset_name_input.value,
                                    randomizer_select.value,
                                    content_editor.value,
                                    description_input.value,
                                    validation_msg
                                )
                            ).classes('btn btn-primary')

    def _validate_yaml(self, content: str, message_label):
        """
        Validate YAML content.

        Args:
            content: YAML content to validate
            message_label: UI label for validation message
        """
        import yaml

        try:
            yaml.safe_load(content)
            message_label.text = '✓ Valid YAML'
            message_label.classes('text-positive')
        except yaml.YAMLError as e:
            message_label.text = f'✗ Invalid YAML: {str(e)}'
            message_label.classes('text-negative')

    async def _save_preset(
        self,
        namespace_name: str,
        preset_name: str,
        randomizer: str,
        content: str,
        description: str,
        message_label
    ):
        """
        Save the preset.

        Args:
            namespace_name: Namespace name
            preset_name: Preset name
            randomizer: Randomizer type
            content: YAML content
            description: Description
            message_label: UI label for messages
        """
        # Validation
        if not preset_name:
            message_label.text = '✗ Preset name is required'
            message_label.classes('text-negative')
            return

        if not content:
            message_label.text = '✗ Content is required'
            message_label.classes('text-negative')
            return

        try:
            if self.is_create:
                # Create new preset
                preset = await self.service.create_preset(
                    namespace_name,
                    preset_name,
                    randomizer,
                    content,
                    self.user,
                    description
                )

                if preset:
                    ui.notify(f'Created preset {preset_name}', type='positive')
                    ui.navigate.to(f'/presets/namespace/{namespace_name}')
                else:
                    message_label.text = '✗ Failed to create preset (check permissions)'
                    message_label.classes('text-negative')
            else:
                # Update existing preset
                success = await self.service.update_preset(
                    self.preset,
                    content=content,
                    description=description,
                    user=self.user
                )

                if success:
                    ui.notify(f'Updated preset {preset_name}', type='positive')
                    ui.navigate.back()
                else:
                    message_label.text = '✗ Failed to update preset (check permissions)'
                    message_label.classes('text-negative')

        except ValueError as e:
            message_label.text = f'✗ {str(e)}'
            message_label.classes('text-negative')
        except Exception as e:
            logger.error("Error saving preset: %s", e, exc_info=True)
            message_label.text = f'✗ Error: {str(e)}'
            message_label.classes('text-negative')
