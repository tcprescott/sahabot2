"""
Organization Requests view for admin panel.

Allows SUPERADMINs to review and approve/reject organization creation requests.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from nicegui import ui
from models import User, OrganizationRequest, Organization, OrganizationMember
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from application.services.organization_service import OrganizationService

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
        # Fetch pending requests
        pending_requests = await OrganizationRequest.filter(
            status=OrganizationRequest.RequestStatus.PENDING
        ).prefetch_related('requested_by').order_by('-requested_at').all()

        # Fetch recently reviewed requests
        reviewed_requests = await OrganizationRequest.filter(
            status__in=[OrganizationRequest.RequestStatus.APPROVED, OrganizationRequest.RequestStatus.REJECTED]
        ).prefetch_related('requested_by', 'reviewed_by').order_by('-reviewed_at').limit(10).all()

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
        with ui.dialog() as approve_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('check_circle').classes('icon-medium')
                            ui.label('Approve Organization Request').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=approve_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    with ui.column().classes('gap-4 w-full'):
                        ui.label(f'Organization: {request.name}').classes('font-bold')
                        if request.description:
                            ui.label(request.description).classes('text-sm text-secondary')
                        ui.label(f'Requested by: {request.requested_by.discord_username}').classes('text-sm')

                        ui.separator()

                        ui.label('Approving this request will:').classes('font-bold mt-2')
                        with ui.column().classes('gap-1 ml-4'):
                            ui.label('• Create the organization').classes('text-sm')
                            ui.label('• Add the requester as an admin member').classes('text-sm')
                            ui.label('• Mark the request as approved').classes('text-sm')

                        notes_input = ui.textarea(
                            label='Notes (optional)',
                            placeholder='Add any notes about this approval'
                        ).classes('w-full mt-4').props('outlined rows=3')

                        # Action buttons
                        with ui.row().classes('justify-end gap-2 mt-4'):
                            ui.button('Cancel', on_click=approve_dialog.close).classes('btn')

                            async def confirm_approve():
                                try:
                                    # Create the organization
                                    org = await Organization.create(
                                        name=request.name,
                                        description=request.description
                                    )

                                    # Add the requester as an admin member
                                    await OrganizationMember.create(
                                        organization=org,
                                        user=request.requested_by,
                                        is_admin=True
                                    )

                                    # Update the request
                                    request.status = OrganizationRequest.RequestStatus.APPROVED
                                    request.reviewed_by = self.user
                                    request.review_notes = notes_input.value if notes_input.value else None
                                    request.reviewed_at = datetime.now(timezone.utc)
                                    await request.save()

                                    ui.notify(f'Organization "{request.name}" created successfully', type='positive')
                                    approve_dialog.close()
                                    await self._refresh()

                                except Exception as e:
                                    logger.error("Failed to approve organization request %s: %s", request.id, e, exc_info=True)
                                    ui.notify(f'Failed to approve request: {str(e)}', type='negative')

                            ui.button('Approve & Create Organization', on_click=confirm_approve).classes('btn').props('color=positive')

        approve_dialog.open()

    async def _show_reject_dialog(self, request: OrganizationRequest) -> None:
        """Show dialog to reject an organization request."""
        with ui.dialog() as reject_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('cancel').classes('icon-medium')
                            ui.label('Reject Organization Request').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=reject_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    with ui.column().classes('gap-4 w-full'):
                        ui.label(f'Organization: {request.name}').classes('font-bold')
                        if request.description:
                            ui.label(request.description).classes('text-sm text-secondary')
                        ui.label(f'Requested by: {request.requested_by.discord_username}').classes('text-sm')

                        ui.separator()

                        notes_input = ui.textarea(
                            label='Rejection Reason',
                            placeholder='Explain why this request is being rejected'
                        ).classes('w-full').props('outlined rows=4')

                        # Action buttons
                        with ui.row().classes('justify-end gap-2 mt-4'):
                            ui.button('Cancel', on_click=reject_dialog.close).classes('btn')

                            async def confirm_reject():
                                try:
                                    # Update the request
                                    request.status = OrganizationRequest.RequestStatus.REJECTED
                                    request.reviewed_by = self.user
                                    request.review_notes = notes_input.value if notes_input.value else None
                                    request.reviewed_at = datetime.now(timezone.utc)
                                    await request.save()

                                    ui.notify('Organization request rejected', type='positive')
                                    reject_dialog.close()
                                    await self._refresh()

                                except Exception as e:
                                    logger.error("Failed to reject organization request %s: %s", request.id, e, exc_info=True)
                                    ui.notify(f'Failed to reject request: {str(e)}', type='negative')

                            ui.button('Reject Request', on_click=confirm_reject).classes('btn').props('color=negative')

        reject_dialog.open()
