"""
Edit Permission Dialog.

Dialog for editing user permissions in a namespace.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import PresetNamespacePermission
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class EditPermissionDialog(BaseDialog):
    """Dialog for editing user permissions."""

    def __init__(self, permission: PresetNamespacePermission, on_save=None):
        """
        Initialize edit permission dialog.

        Args:
            permission: Permission to edit
            on_save: Callback after successful save
        """
        super().__init__()
        self.permission = permission
        self.on_save = on_save
        self.can_create_cb = None
        self.can_update_cb = None
        self.can_delete_cb = None

    async def show(self):
        """Display the dialog."""
        await self.permission.fetch_related("user")
        self.create_dialog(
            title=f"Edit Permissions: {self.permission.user.get_display_name()}",
            icon="edit",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        # Permission checkboxes
        self.can_create_cb = ui.checkbox(
            "Can Create Presets", value=self.permission.can_create
        )
        self.can_update_cb = ui.checkbox(
            "Can Update Presets", value=self.permission.can_update
        )
        self.can_delete_cb = ui.checkbox(
            "Can Delete Presets", value=self.permission.can_delete
        )

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
            await self.permission.fetch_related("namespace")
            self.permission.can_create = self.can_create_cb.value
            self.permission.can_update = self.can_update_cb.value
            self.permission.can_delete = self.can_delete_cb.value
            await self.permission.save()

            ui.notify("Permissions updated successfully", type="positive")
            await self.close()
            if self.on_save:
                await self.on_save()

        except Exception as e:
            logger.error("Failed to update permission: %s", e, exc_info=True)
            ui.notify(f"Failed to update permission: {str(e)}", type="negative")
