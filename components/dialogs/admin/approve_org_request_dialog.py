"""
Approve Organization Request Dialog.

Dialog for approving an organization request.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from nicegui import ui
from models import User, OrganizationRequest, Organization
from models.organizations import OrganizationMember
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class ApproveOrgRequestDialog(BaseDialog):
    """Dialog for approving an organization request."""

    def __init__(self, request: OrganizationRequest, user: User, on_save=None):
        """
        Initialize approve request dialog.

        Args:
            request: Organization request to approve
            user: Current user (reviewer)
            on_save: Callback after successful approval
        """
        super().__init__()
        self.request = request
        self.user = user
        self.on_save = on_save
        self.notes_input = None

    async def show(self):
        """Display the dialog."""
        await self.request.fetch_related("requested_by")
        self.create_dialog(
            title="Approve Organization Request",
            icon="check_circle",
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        ui.label(f"Organization: {self.request.name}").classes("font-bold mb-2")
        if self.request.description:
            ui.label(self.request.description).classes("text-sm text-secondary mb-2")
        ui.label(f"Requested by: {self.request.requested_by.discord_username}").classes(
            "text-sm mb-4"
        )

        ui.separator()

        ui.label("Approving this request will:").classes("font-bold mt-2 mb-2")
        with ui.column().classes("gap-1 ml-4 mb-4"):
            ui.label("• Create the organization").classes("text-sm")
            ui.label("• Add the requester as an admin member").classes("text-sm")
            ui.label("• Mark the request as approved").classes("text-sm")

        self.notes_input = (
            ui.textarea(
                label="Notes (optional)",
                placeholder="Add any notes about this approval",
            )
            .classes("w-full")
            .props("outlined rows=3")
        )

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button("Cancel", on_click=self.close).classes("btn")
            ui.button("Approve & Create Organization", on_click=self._approve).classes(
                "btn"
            ).props("color=positive")

    async def _approve(self):
        """Approve the request and create organization."""
        try:
            # Create the organization
            org = await Organization.create(
                name=self.request.name, description=self.request.description
            )

            # Add the requester as an admin member
            await OrganizationMember.create(
                organization=org, user=self.request.requested_by, is_admin=True
            )

            # Update the request
            self.request.status = OrganizationRequest.RequestStatus.APPROVED
            self.request.reviewed_by = self.user
            self.request.review_notes = (
                self.notes_input.value if self.notes_input.value else None
            )
            self.request.reviewed_at = datetime.now(timezone.utc)
            await self.request.save()

            ui.notify(
                f'Organization "{self.request.name}" created successfully',
                type="positive",
            )
            await self.close()
            if self.on_save:
                await self.on_save()

        except Exception as e:
            logger.error(
                "Failed to approve organization request %s: %s",
                self.request.id,
                e,
                exc_info=True,
            )
            ui.notify(f"Failed to approve request: {str(e)}", type="negative")
