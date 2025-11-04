"""
View namespace dialog component.

Displays detailed information about a preset namespace.
"""
from nicegui import ui
from components.dialogs.common.base_dialog import BaseDialog
from components.datetime_label import DateTimeLabel
from models.preset_namespace import PresetNamespace


class ViewNamespaceDialog(BaseDialog):
    """Dialog for viewing namespace details."""

    def __init__(self, namespace: PresetNamespace):
        """
        Initialize view namespace dialog.

        Args:
            namespace: Namespace to view (should be prefetched with 'user', 'organization', 'presets')
        """
        super().__init__()
        self.namespace = namespace

    async def show(self) -> None:
        """Display the view namespace dialog."""
        self.create_dialog(
            title=f'Namespace: {self.namespace.display_name}',
            icon='visibility',
            max_width='dialog-card'
        )
        await super().show()

    def _render_body(self) -> None:
        """Render dialog content."""
        namespace = self.namespace

        # Details section
        with ui.column().classes('gap-3 w-full'):
            # Name
            with ui.element('div'):
                ui.label('Name:').classes('font-bold')
                ui.label(namespace.name).classes('font-mono')

            # Display Name
            with ui.element('div'):
                ui.label('Display Name:').classes('font-bold')
                ui.label(namespace.display_name)

            # Description
            if namespace.description:
                with ui.element('div'):
                    ui.label('Description:').classes('font-bold')
                    ui.label(namespace.description)

            # Owner
            with ui.element('div'):
                ui.label('Owner:').classes('font-bold')
                if namespace.user:
                    ui.label(f'User: {namespace.user.get_display_name()}')
                elif namespace.organization:
                    ui.label(f'Organization: {namespace.organization.name}')
                else:
                    ui.label('System')

            # Visibility
            with ui.element('div'):
                ui.label('Visibility:').classes('font-bold')
                ui.label('Public' if namespace.is_public else 'Private')

            # Preset count
            with ui.element('div'):
                ui.label('Presets:').classes('font-bold')
                ui.label(f'{len(namespace.presets)} preset(s)')

            # Timestamps
            with ui.element('div'):
                ui.label('Created:').classes('font-bold')
                DateTimeLabel.create(namespace.created_at)

            with ui.element('div'):
                ui.label('Updated:').classes('font-bold')
                DateTimeLabel.create(namespace.updated_at)

        ui.separator()

        # Actions
        with self.create_actions_row():
            ui.button('Close', on_click=self.close).classes('btn')
