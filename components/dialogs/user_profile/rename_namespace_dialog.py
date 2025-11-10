"""
Rename Namespace Dialog.

Dialog for renaming a preset namespace.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import PresetNamespace
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class RenameNamespaceDialog(BaseDialog):
    """Dialog for renaming a preset namespace."""

    def __init__(self, namespace: PresetNamespace, on_save=None):
        """
        Initialize rename namespace dialog.

        Args:
            namespace: Namespace to rename
            on_save: Callback after successful save
        """
        super().__init__()
        self.namespace = namespace
        self.on_save = on_save
        self.display_name_input = None
        self.description_input = None
        self.visibility_checkbox = None

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title="Rename Namespace",
            icon="edit",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        ui.label(f"Current name: {self.namespace.display_name}").classes(
            "text-sm text-secondary mb-4"
        )

        # Input fields
        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self.display_name_input = (
                    ui.input(label="Display Name", value=self.namespace.display_name)
                    .classes("w-full")
                    .props("outlined")
                )

            with ui.element("div"):
                self.description_input = (
                    ui.textarea(
                        label="Description (optional)",
                        value=self.namespace.description or "",
                    )
                    .classes("w-full")
                    .props("outlined")
                )

        # Visibility toggle
        self.visibility_checkbox = ui.checkbox(
            "Public (visible to all users)", value=self.namespace.is_public
        ).classes("mt-4")

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Save", on_click=self._save).classes("btn").props(
                "color=positive"
            )

    async def _save(self):
        """Save changes and close."""
        try:
            self.namespace.display_name = self.display_name_input.value
            self.namespace.description = self.description_input.value or None
            self.namespace.is_public = self.visibility_checkbox.value
            await self.namespace.save()
            ui.notify("Namespace updated successfully", type="positive")
            await self.close()
            if self.on_save:
                await self.on_save()
        except Exception as e:
            logger.error(
                "Failed to update namespace %s: %s", self.namespace.id, e, exc_info=True
            )
            ui.notify(f"Failed to update namespace: {str(e)}", type="negative")
