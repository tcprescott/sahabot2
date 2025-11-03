"""
Preset Editor Dialog for creating/editing randomizer presets.

This dialog provides a YAML editor with syntax highlighting and validation
for creating and editing randomizer presets.
"""

from __future__ import annotations
from nicegui import ui
from typing import Optional, Callable
from components.dialogs.common.base_dialog import BaseDialog
from models import RandomizerPreset


class PresetEditorDialog(BaseDialog):
    """Dialog for creating/editing randomizer presets with YAML editor."""

    RANDOMIZERS = [
        {'label': 'A Link to the Past Randomizer', 'value': 'alttpr'},
        {'label': 'Super Metroid', 'value': 'sm'},
        {'label': 'SMZ3 Combo', 'value': 'smz3'},
        {'label': 'Ocarina of Time Randomizer', 'value': 'ootr'},
        {'label': 'Aria of Sorrow Randomizer', 'value': 'aosr'},
        {'label': 'Zelda 1 Randomizer', 'value': 'z1r'},
        {'label': 'Final Fantasy Randomizer', 'value': 'ffr'},
        {'label': 'Super Mario Bros 3 Randomizer', 'value': 'smb3r'},
        {'label': 'Chrono Trigger: Jets of Time', 'value': 'ctjets'},
        {'label': 'Bingosync', 'value': 'bingosync'},
    ]

    def __init__(
        self,
        preset: Optional[RandomizerPreset] = None,
        organization_id: Optional[int] = None,
        is_global: bool = False,
        on_save: Optional[Callable] = None
    ):
        """
        Initialize the preset editor dialog.

        Args:
            preset: Existing preset to edit (None for new)
            organization_id: Organization ID for org presets (deprecated, use namespaces)
            is_global: Whether to create a global preset (requires SUPERADMIN)
            on_save: Callback after save
        """
        super().__init__()
        self.preset = preset
        self.organization_id = organization_id
        self.is_global = is_global
        self.on_save = on_save
        self.is_edit_mode = preset is not None

        # Form fields
        self.name_input = None
        self.randomizer_select = None
        self.description_input = None
        self.is_public_checkbox = None
        self.yaml_editor = None
        self.validation_message = None

    async def show(self):
        """Display the dialog."""
        if self.is_edit_mode:
            title = f"Edit Preset: {self.preset.name}"
        elif self.is_global:
            title = "Create New Global Preset"
        else:
            title = "Create New Preset"
        
        self.create_dialog(
            title=title,
            icon='edit' if self.is_edit_mode else 'add',
            max_width='900px'
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Include CodeMirror CSS and JS
        ui.add_head_html('''
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@6.0.1/dist/index.css">
            <script src="https://cdn.jsdelivr.net/npm/codemirror@6.0.1/dist/index.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@codemirror/lang-yaml@6.0.0/dist/index.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/@codemirror/theme-one-dark@6.0.0/dist/index.js"></script>
        ''')

        # Basic info section
        with self.create_form_grid(columns=2):
            with ui.element('div'):
                self.name_input = ui.input(
                    label='Preset Name',
                    placeholder='e.g., open, standard, keysanity'
                ).classes('w-full').props('outlined dense')
                if self.preset:
                    self.name_input.value = self.preset.name
                    if self.is_edit_mode:
                        self.name_input.props('readonly')  # Can't change name in edit mode

            with ui.element('div'):
                self.randomizer_select = ui.select(
                    label='Randomizer',
                    options=self.RANDOMIZERS,
                    value=self.preset.randomizer if self.preset else 'alttpr'
                ).classes('w-full').props('outlined dense')
                if self.is_edit_mode:
                    self.randomizer_select.props('readonly')  # Can't change randomizer in edit mode

        # Description
        with ui.element('div').classes('mt-4'):
            self.description_input = ui.textarea(
                label='Description (optional)',
                placeholder='Describe what this preset does...'
            ).classes('w-full').props('outlined dense rows=2')
            if self.preset and self.preset.description:
                self.description_input.value = self.preset.description

        # Public checkbox
        with ui.element('div').classes('mt-4'):
            self.is_public_checkbox = ui.checkbox(
                'Make this preset public (visible to all organization members)',
                value=self.preset.is_public if self.preset else False
            )

        ui.separator().classes('my-4')

        # YAML Editor Section
        with ui.element('div'):
            ui.label('YAML Configuration').classes('text-lg font-bold mb-2')
            ui.label('Edit the preset settings in YAML format below:').classes('text-sm text-secondary mb-2')

            # CodeMirror container
            self.yaml_editor = ui.element('div').classes('border rounded').style('min-height: 400px')

            # Initialize CodeMirror
            default_yaml = self._get_default_yaml()
            self.yaml_editor.run_method(
                'innerHTML',
                '''<div id="codemirror-editor" style="height: 400px;"></div>
                <script>
                    if (typeof window.editorView !== 'undefined') {
                        window.editorView.destroy();
                    }
                    
                    const { EditorView, basicSetup } = CM["@codemirror/basic-setup"] || CM;
                    const { yaml } = CM["@codemirror/lang-yaml"] || CM;
                    const { oneDark } = CM["@codemirror/theme-one-dark"] || CM;
                    
                    const startState = EditorView.state.create({
                        doc: `''' + default_yaml.replace('`', '\\`').replace('${', '\\${') + '''`,
                        extensions: [
                            basicSetup,
                            yaml(),
                            EditorView.lineWrapping,
                            EditorView.theme({
                                "&": { height: "400px" },
                                ".cm-scroller": { overflow: "auto" }
                            })
                        ]
                    });
                    
                    window.editorView = new EditorView({
                        state: startState,
                        parent: document.getElementById('codemirror-editor')
                    });
                </script>'''
            )

            # Validation message area
            self.validation_message = ui.element('div').classes('mt-2')

        ui.separator().classes('my-4')

        # Action buttons
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Validate', on_click=self._validate_yaml, icon='check_circle').classes('btn').props('color=primary')
            ui.button(
                'Save' if self.is_edit_mode else 'Create',
                on_click=self._save,
                icon='save'
            ).classes('btn').props('color=positive')

    def _get_default_yaml(self) -> str:
        """Get default YAML content for editor."""
        if self.preset and self.preset.settings:
            # Convert settings dict back to YAML
            import yaml
            return yaml.dump(self.preset.settings, default_flow_style=False, sort_keys=False)

        # Default template for new preset
        return '''# Preset Configuration
# Edit the settings below according to your randomizer's requirements

description: "Your preset description here"
settings:
  # Add your randomizer settings here
  # Example for ALTTPR:
  goal: ganon
  mode: open
  weapons: randomized
  # ... add more settings as needed
'''

    async def _validate_yaml(self):
        """Validate YAML content."""
        # Get YAML from CodeMirror
        yaml_content = await ui.run_javascript(
            'window.editorView.state.doc.toString()',
            timeout=5.0
        )

        if not yaml_content:
            self.validation_message.clear()
            with self.validation_message:
                with ui.element('div').classes('p-2 rounded bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'):
                    ui.icon('error').classes('mr-2')
                    ui.label('YAML content is empty')
            return False

        # Validate via service
        from application.services.randomizer_preset_service import (
            RandomizerPresetService,
            PresetValidationError
        )

        try:
            service = RandomizerPresetService()
            service.validate_yaml_content(yaml_content)

            # Show success
            self.validation_message.clear()
            with self.validation_message:
                with ui.element('div').classes('p-2 rounded bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'):
                    ui.icon('check_circle').classes('mr-2')
                    ui.label('YAML is valid!')

            return True

        except PresetValidationError as e:
            self.validation_message.clear()
            with self.validation_message:
                with ui.element('div').classes('p-2 rounded bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'):
                    ui.icon('error').classes('mr-2')
                    ui.label(f'Validation Error: {str(e)}')
            return False

    async def _save(self):
        """Save the preset."""
        # Validate inputs
        name = self.name_input.value.strip() if self.name_input.value else ''
        if not name:
            ui.notify('Please enter a preset name', type='negative')
            return

        randomizer = self.randomizer_select.value
        if not randomizer:
            ui.notify('Please select a randomizer', type='negative')
            return

        # Get and validate YAML
        yaml_content = await ui.run_javascript(
            'window.editorView.state.doc.toString()',
            timeout=5.0
        )

        if not yaml_content:
            ui.notify('Please enter YAML configuration', type='negative')
            return

        # Validate first
        if not await self._validate_yaml():
            ui.notify('Please fix validation errors before saving', type='negative')
            return

        # Get current user from session
        from nicegui import app
        user = app.storage.user.get('user')
        if not user:
            ui.notify('User not authenticated', type='negative')
            return

        # Save via service
        from application.services.randomizer_preset_service import (
            RandomizerPresetService,
            PresetValidationError
        )
        from models import User

        try:
            service = RandomizerPresetService()
            user_obj = await User.get(id=user['id'])

            description = self.description_input.value.strip() if self.description_input.value else None
            is_public = self.is_public_checkbox.value

            if self.is_edit_mode:
                # Update existing preset
                await service.update_preset(
                    preset_id=self.preset.id,
                    user=user_obj,
                    yaml_content=yaml_content,
                    description=description,
                    is_public=is_public
                )
                ui.notify(f'Preset "{name}" updated successfully', type='positive')
            else:
                # Create new preset
                await service.create_preset(
                    user=user_obj,
                    randomizer=randomizer,
                    name=name,
                    yaml_content=yaml_content,
                    description=description,
                    is_public=is_public,
                    is_global=self.is_global
                )
                scope = "global preset" if self.is_global else "preset"
                ui.notify(f'{scope.title()} "{name}" created successfully', type='positive')

            # Call callback
            if self.on_save:
                await self.on_save()

            # Close dialog
            await self.close()

        except PresetValidationError as e:
            ui.notify(f'Validation error: {str(e)}', type='negative')
        except PermissionError as e:
            ui.notify(f'Permission denied: {str(e)}', type='negative')
        except Exception as e:
            ui.notify(f'Error saving preset: {str(e)}', type='negative')
