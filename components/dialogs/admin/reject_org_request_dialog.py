"""
Reject Organization Request Dialog.

Dialog for rejecting an organization request.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from nicegui import ui
from models import User, OrganizationRequest
from components.dialogs.common.base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class RejectOrgRequestDialog(BaseDialog):
    """Dialog for rejecting an organization request."""

    def __init__(self, request: OrganizationRequest, user: User, on_save=None):
        """
        Initialize reject request dialog.

        Args:
            request: Organization request to reject
            user: Current user (reviewer)
            on_save: Callback after successful rejection
        """
        super().__init__()
        self.request = request
        self.user = user
        self.on_save = on_save
        self.notes_input = None

    async def show(self):
        """Display the dialog."""
        await self.request.fetch_related('requested_by')
        self.create_dialog(
            title='Reject Organization Request',
            icon='cancel',
        )
        await super().show()

    def _render_body(self):
        """Render dialog content."""
        ui.label(f'Organization: {self.request.name}').classes('font-bold mb-2')
        if self.request.description:
            ui.label(self.request.description).classes('text-sm text-secondary mb-2')
        ui.label(f'Requested by: {self.request.requested_by.discord_username}').classes('text-sm mb-4')

        ui.separator()

        self.notes_input = ui.textarea(
            label='Rejection Reason',
            placeholder='Explain why this request is being rejected'
        ).classes('w-full').props('outlined rows=4')

        ui.separator()

        # Actions row
        with self.create_actions_row():
            ui.button('Cancel', on_click=self.close).classes('btn')
            ui.button('Reject Request', on_click=self._reject).classes('btn').props('color=negative')

    async def _reject(self):
        """Reject the request."""
        try:
            # Update the request
            self.request.status = OrganizationRequest.RequestStatus.REJECTED
            self.request.reviewed_by = self.user
            self.request.review_notes = self.notes_input.value if self.notes_input.value else None
            self.request.reviewed_at = datetime.now(timezone.utc)
            await self.request.save()

            ui.notify('Organization request rejected', type='positive')
            await self.close()
            if self.on_save:
                await self.on_save()

        except Exception as e:
            logger.error("Failed to reject organization request %s: %s", self.request.id, e, exc_info=True)
            ui.notify(f'Failed to reject request: {str(e)}', type='negative')
