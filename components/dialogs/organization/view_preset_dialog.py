"""
View Preset Dialog.

Dialog for viewing preset details including YAML configuration.
"""

from __future__ import annotations
import logging
import yaml
from nicegui import ui
from models import RandomizerPreset
from components.dialogs.common.base_dialog import BaseDialog
from components.datetime_label import DateTimeLabel

logger = logging.getLogger(__name__)


class ViewPresetDialog(BaseDialog):
    """Dialog for viewing preset details."""

    # Randomizer display labels
    RANDOMIZER_LABELS = {
        "alttpr": "ALttPR",
        "smz3": "SMZ3",
        "sm": "Super Metroid",
    }

    def __init__(self, preset: RandomizerPreset):
        """
        Initialize view preset dialog.

        Args:
            preset: Preset to view
        """
        super().__init__()
        self.preset = preset

    async def show(self):
        """Display the dialog."""
        await self.preset.fetch_related("user")
        self.create_dialog(title="View Preset", icon="visibility", max_width="900px")
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Header with preset name and randomizer badge
        with ui.row().classes("items-center gap-2 mb-4"):
            ui.label(self.preset.name).classes("text-xl font-bold")
            randomizer_label = self.RANDOMIZER_LABELS.get(
                self.preset.randomizer, self.preset.randomizer
            )
            with ui.element("span").classes("badge badge-secondary"):
                ui.label(randomizer_label)

        # Description
        if self.preset.description:
            self.create_section_title("Description")
            ui.label(self.preset.description).classes("text-sm mb-4")

        # Metadata
        self.create_section_title("Metadata")
        with ui.column().classes("gap-2 mb-4"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("person", size="sm")
                ui.label(f"Created by: {self.preset.user.get_display_name()}").classes(
                    "text-sm"
                )

            with ui.row().classes("items-center gap-2"):
                ui.icon("update", size="sm")
                ui.label("Updated:").classes("text-sm")
                DateTimeLabel.create(
                    self.preset.updated_at, format_type="datetime", classes="text-sm"
                )

            with ui.row().classes("items-center gap-2"):
                ui.icon(
                    "visibility" if self.preset.is_public else "visibility_off",
                    size="sm",
                )
                if self.preset.is_public:
                    ui.label("Visibility: Public").classes("text-sm")
                else:
                    ui.label("Visibility: Private").classes("text-sm text-secondary")

        ui.separator()

        # YAML content
        self.create_section_title("YAML Configuration")
        yaml_content = yaml.dump(
            self.preset.settings, default_flow_style=False, sort_keys=False
        )
        with ui.element("pre").classes(
            "bg-gray-100 dark:bg-gray-800 p-4 rounded overflow-x-auto"
        ):
            ui.label(yaml_content).classes("text-sm font-mono")

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button("Close", on_click=self.close).classes("btn")
            ui.button(
                "Copy YAML", icon="content_copy", on_click=self._copy_yaml
            ).classes("btn").props("color=primary")

    async def _copy_yaml(self):
        """Copy YAML to clipboard."""
        yaml_content = yaml.dump(
            self.preset.settings, default_flow_style=False, sort_keys=False
        )
        # Escape backticks for JavaScript
        escaped_yaml = yaml_content.replace("`", "\\`").replace("\\", "\\\\")
        success = await ui.run_javascript(
            f"return window.ClipboardUtils.copy(`{escaped_yaml}`);"
        )
        if success:
            ui.notify("YAML copied to clipboard", type="positive")
        else:
            ui.notify("Failed to copy YAML", type="negative")
