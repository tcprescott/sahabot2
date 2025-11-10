"""
View YAML Dialog.

Dialog for viewing preset YAML configuration.
"""

from __future__ import annotations
import logging
import yaml
from nicegui import ui
from models import RandomizerPreset
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class ViewYamlDialog(BaseDialog):
    """Dialog for viewing preset YAML."""

    # Randomizer display labels
    RANDOMIZER_LABELS = {
        "alttpr": "ALttPR",
        "smz3": "SMZ3",
        "sm": "Super Metroid",
    }

    def __init__(self, preset: RandomizerPreset):
        """
        Initialize view YAML dialog.

        Args:
            preset: Preset to view
        """
        super().__init__()
        self.preset = preset
        self.yaml_content = ""

    async def show(self):
        """Display the dialog."""
        await self.preset.fetch_related("user", "namespace")

        # Format YAML
        try:
            self.yaml_content = yaml.dump(
                self.preset.settings, default_flow_style=False, sort_keys=False
            )
        except Exception as e:
            self.yaml_content = f"Error formatting YAML: {e}"

        self.create_dialog(
            title=f"Preset: {self.preset.name}", icon="visibility", max_width="800px"
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Metadata section
        with ui.column().classes("gap-2 mb-4"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("category", size="sm")
                randomizer_label = self.RANDOMIZER_LABELS.get(
                    self.preset.randomizer, self.preset.randomizer
                )
                ui.label(f"Randomizer: {randomizer_label}").classes("text-sm")

            if self.preset.description:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("description", size="sm")
                    ui.label(f"Description: {self.preset.description}").classes(
                        "text-sm"
                    )

            # Scope
            with ui.row().classes("items-center gap-2"):
                if self.preset.namespace:
                    ui.icon("folder", size="sm")
                    ui.label(
                        f"Namespace: {self.preset.namespace.display_name}"
                    ).classes("text-sm")
                else:
                    ui.icon("public", size="sm")
                    ui.label("Scope: Global").classes("text-sm font-bold")

            # Creator
            if self.preset.user:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("person", size="sm")
                    ui.label(
                        f"Created by: {self.preset.user.get_display_name()}"
                    ).classes("text-sm")

            # Visibility
            with ui.row().classes("items-center gap-2"):
                ui.icon("visibility", size="sm")
                visibility = "Public" if self.preset.is_public else "Private"
                ui.label(f"Visibility: {visibility}").classes("text-sm")

        ui.separator()

        # YAML content
        self.create_section_title("YAML Content")
        ui.code(self.yaml_content, language="yaml").classes("w-full").style(
            "max-height: 400px; overflow-y: auto;"
        )

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button("Close", on_click=self.close).classes("btn")
            ui.button(
                "Copy YAML", icon="content_copy", on_click=self._copy_yaml
            ).classes("btn").props("color=primary")

    async def _copy_yaml(self):
        """Copy YAML to clipboard."""
        success = await ui.run_javascript(
            f"return window.ClipboardUtils.copy({self.yaml_content!r});"
        )
        if success:
            ui.notify("YAML copied to clipboard!", type="positive")
        else:
            ui.notify("Failed to copy YAML", type="negative")
