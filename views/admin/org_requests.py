"""
Organization Requests view for admin panel.

Allows SUPERADMINs to review and approve/reject organization creation requests.
"""

from __future__ import annotations
import logging
from nicegui import ui
from models import User, OrganizationRequest
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from components.dialogs.admin import ApproveOrgRequestDialog, RejectOrgRequestDialog
from application.services.organizations.organization_service import OrganizationService

logger = logging.getLogger(__name__)


class OrgRequestsView:
    """View for managing organization creation requests."""

    def __init__(self, user: User):
        """
        Initialize the organization requests view.

        Args:
            user: Current user (must be SUPERADMIN)
        """
        self.user = user
        self.service = OrganizationService()
        self.container = None

    async def render(self) -> None:
        """Render the organization requests view."""
        with ui.column().classes('w-full gap-4') as self.container:
            # Page header
            with ui.row().classes('items-center justify-between w-full'):
                with ui.column().classes('gap-1'):
                    ui.label('Organization Requests').classes('text-2xl font-bold')
                    ui.label('Review and approve requests for new organizations.').classes('text-secondary')

            await self._render_content()

    async def _render_content(self) -> None:
        """Render the main content."""
        # Import organization request service
        from application.services.organizations.organization_request_service import OrganizationRequestService

        request_service = OrganizationRequestService()

        # Fetch pending requests (using service layer)
        pending_requests = await request_service.list_pending_requests(self.user)

        # Fetch recently reviewed requests (using service layer)
        reviewed_requests = await request_service.list_reviewed_requests(self.user)

        # Pending requests section
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('Pending Requests').classes('text-xl font-bold')

            with ui.element('div').classes('card-body'):
                if not pending_requests:
                    with ui.element('div').classes('text-center py-4'):
                        ui.icon('check_circle').classes('text-positive icon-large')
                        ui.label('No pending requests').classes('text-secondary')
                else:
                    async def render_name_cell(request):
                        with ui.column().classes('gap-1'):
                            ui.label(request.name).classes('font-bold')
                            if request.description:
                                ui.label(request.description).classes('text-sm text-secondary')

                    async def render_requested_by_cell(request):
                        ui.label(request.requested_by.discord_username).classes('text-sm')

                    async def render_requested_at_cell(request):
                        DateTimeLabel.create(request.requested_at)

                    async def render_actions_cell(request):
                        with ui.row().classes('gap-1'):
                            # Approve button
                            async def approve():
                                await self._show_approve_dialog(request)

                            ui.button(
                                icon='check_circle',
                                on_click=approve
                            ).classes('btn btn-sm').props('flat color=positive').tooltip('Approve Request')

                            # Reject button
                            async def reject():
                                await self._show_reject_dialog(request)

                            ui.button(
                                icon='cancel',
                                on_click=reject
                            ).classes('btn btn-sm').props('flat color=negative').tooltip('Reject Request')

                    columns = [
                        TableColumn(label='Organization Name', cell_render=render_name_cell),
                        TableColumn(label='Requested By', cell_render=render_requested_by_cell),
                        TableColumn(label='Requested At', cell_render=render_requested_at_cell),
                        TableColumn(label='Actions', cell_render=render_actions_cell),
                    ]

                    table = ResponsiveTable(columns=columns, rows=pending_requests)
                    await table.render()

        # Recently reviewed section
        if reviewed_requests:
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Recently Reviewed').classes('text-xl font-bold')

                with ui.element('div').classes('card-body'):
                    async def render_reviewed_name_cell(request):
                        with ui.column().classes('gap-1'):
                            ui.label(request.name).classes('font-bold')
                            if request.description:
                                ui.label(request.description).classes('text-sm text-secondary')

                    async def render_status_cell(request):
                        if request.is_approved:
                            with ui.element('span').classes('badge badge-success'):
                                ui.label('Approved')
                        else:
                            with ui.element('span').classes('badge badge-danger'):
                                ui.label('Rejected')

                    async def render_reviewed_by_cell(request):
                        if request.reviewed_by:
                            ui.label(request.reviewed_by.discord_username).classes('text-sm')
                        else:
                            ui.label('—').classes('text-secondary')

                    async def render_reviewed_at_cell(request):
                        if request.reviewed_at:
                            DateTimeLabel.create(request.reviewed_at)
                        else:
                            ui.label('—').classes('text-secondary')

                    reviewed_columns = [
                        TableColumn(label='Organization Name', cell_render=render_reviewed_name_cell),
                        TableColumn(label='Status', cell_render=render_status_cell),
                        TableColumn(label='Reviewed By', cell_render=render_reviewed_by_cell),
                        TableColumn(label='Reviewed At', cell_render=render_reviewed_at_cell),
                    ]

                    reviewed_table = ResponsiveTable(columns=reviewed_columns, rows=reviewed_requests)
                    await reviewed_table.render()

    async def _refresh(self) -> None:
        """Refresh the content."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _show_approve_dialog(self, request: OrganizationRequest) -> None:
        """Show dialog to approve an organization request."""
        dialog = ApproveOrgRequestDialog(request=request, user=self.user, on_save=self._refresh)
        await dialog.show()

    async def _show_reject_dialog(self, request: OrganizationRequest) -> None:
        """Show dialog to reject an organization request."""
        dialog = RejectOrgRequestDialog(request=request, user=self.user, on_save=self._refresh)
        await dialog.show()
