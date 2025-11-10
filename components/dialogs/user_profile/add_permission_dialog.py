"""
Add Permission Dialog.

Dialog for adding user permissions to a namespace.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User, PresetNamespace, PresetNamespacePermission
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class AddPermissionDialog(BaseDialog):
    """Dialog for adding user permissions to a namespace."""

    def __init__(self, namespace: PresetNamespace, on_save=None):
        """
        Initialize add permission dialog.

        Args:
            namespace: Namespace to add permissions for
            on_save: Callback after successful save
        """
        super().__init__()
        self.namespace = namespace
        self.on_save = on_save
        self.username_input = None
        self.can_create_cb = None
        self.can_update_cb = None
        self.can_delete_cb = None

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title="Add User Permission",
            icon="person_add",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        ui.label(
            "Enter the Discord username of the user you want to grant permissions to:"
        ).classes("text-sm mb-4")

        # Username input
        self.username_input = (
            ui.input(label="Discord Username", placeholder="username")
            .classes("w-full mb-4")
            .props("outlined")
        )

        ui.separator()

        # Permission checkboxes
        self.create_section_title("Permissions")
        self.can_create_cb = ui.checkbox("Can Create Presets", value=True)
        self.can_update_cb = ui.checkbox("Can Update Presets", value=True)
        self.can_delete_cb = ui.checkbox("Can Delete Presets", value=False)

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Add", on_click=self._save).classes("btn").props("color=positive")

    async def _save(self):
        """Add permission and close."""
        try:
            # Find user by username
            target_user = await User.filter(
                discord_username__iexact=self.username_input.value
            ).first()

            if not target_user:
                ui.notify("User not found", type="negative")
                return

            # Check if permission already exists
            existing = await PresetNamespacePermission.filter(
                namespace_id=self.namespace.id, user_id=target_user.id
            ).first()

            if existing:
                ui.notify(
                    "User already has permissions in this namespace", type="warning"
                )
                return

            # Create permission
            await PresetNamespacePermission.create(
                namespace=self.namespace,
                user=target_user,
                can_create=self.can_create_cb.value,
                can_update=self.can_update_cb.value,
                can_delete=self.can_delete_cb.value,
            )

            ui.notify("User permission added successfully", type="positive")
            await self.close()
            if self.on_save:
                await self.on_save()

        except Exception as e:
            logger.error("Failed to add permission: %s", e, exc_info=True)
            ui.notify(f"Failed to add permission: {str(e)}", type="negative")
