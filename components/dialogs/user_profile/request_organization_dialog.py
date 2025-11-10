"""
Request Organization Dialog.

Dialog for requesting a new organization.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User, OrganizationRequest
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class RequestOrganizationDialog(BaseDialog):
    """Dialog for requesting a new organization."""

    def __init__(self, user: User, on_save=None):
        """
        Initialize request organization dialog.

        Args:
            user: User requesting the organization
            on_save: Callback after successful save
        """
        super().__init__()
        self.user = user
        self.on_save = on_save
        self.name_input = None
        self.description_input = None

    async def show(self):
        """Display the dialog."""
        self.create_dialog(
            title="Request New Organization",
            icon="add_business",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        ui.label(
            "Submit a request to create a new organization. A SUPERADMIN will review your request."
        ).classes("text-sm text-secondary mb-4")

        # Input fields
        with self.create_form_grid(columns=1):
            with ui.element("div"):
                self.name_input = (
                    ui.input(
                        label="Organization Name", placeholder="Enter organization name"
                    )
                    .classes("w-full")
                    .props("outlined")
                )

            with ui.element("div"):
                self.description_input = (
                    ui.textarea(
                        label="Description",
                        placeholder="Describe the purpose of this organization",
                    )
                    .classes("w-full")
                    .props("outlined rows=4")
                )

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Submit Request", on_click=self._submit).classes("btn").props(
                "color=positive"
            )

    async def _submit(self):
        """Submit the request and close."""
        if not self.name_input.value or not self.name_input.value.strip():
            ui.notify("Organization name is required", type="warning")
            return

        try:
            # Create the request
            await OrganizationRequest.create(
                name=self.name_input.value.strip(),
                description=(
                    self.description_input.value.strip()
                    if self.description_input.value
                    else None
                ),
                requested_by=self.user,
                status=OrganizationRequest.RequestStatus.PENDING,
            )

            ui.notify(
                "Organization request submitted successfully. A SUPERADMIN will review it.",
                type="positive",
            )
            await self.close()
            if self.on_save:
                await self.on_save()

        except Exception as e:
            logger.error("Failed to create organization request: %s", e, exc_info=True)
            ui.notify(f"Failed to submit request: {str(e)}", type="negative")
