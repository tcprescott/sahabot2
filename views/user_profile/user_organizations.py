"""
User Organizations view.

Display organizations the user is a member of and allow navigation to admin panels.
"""

from __future__ import annotations
from nicegui import ui
from models import User, OrganizationRequest
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs import LeaveOrganizationDialog
from application.services.organization_service import OrganizationService
from application.services.authorization_service import AuthorizationService
import logging

logger = logging.getLogger(__name__)


class UserOrganizationsView:
    """View for displaying user's organizations."""

    def __init__(self, user: User) -> None:
        self.user = user
        self.service = OrganizationService()
        self.auth_service = AuthorizationService()
        self.container = None

    async def _refresh(self) -> None:
        """Refresh the organizations list."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _leave_organization(self, org_id: int, org_name: str) -> None:
        """Leave an organization."""
        async def confirm_leave():
            """Handle the leave confirmation."""
            try:
                # Remove the member
                member = await self.service.get_member(org_id, self.user.id)
                if member:
                    await member.delete()
                    ui.notify(f'Left {org_name}', type='positive')
                    await self._refresh()
            except Exception as e:
                logger.error("Failed to leave organization: %s", e)
                ui.notify(f'Failed to leave organization: {e}', type='negative')

        # Show confirmation dialog
        dialog = LeaveOrganizationDialog(org_name, on_confirm=confirm_leave)
        await dialog.show()

    async def _render_content(self) -> None:
        """Render the organizations list."""
        # Get all organization memberships for this user
        from models.organizations import OrganizationMember
        memberships = await OrganizationMember.filter(user_id=self.user.id).prefetch_related('organization', 'permissions')

        # Organization requests section
        pending_requests = await OrganizationRequest.filter(
            requested_by_id=self.user.id,
            status=OrganizationRequest.RequestStatus.PENDING
        ).all()

        if pending_requests:
            with Card.create(title='Pending Organization Requests'):
                with ui.column().classes('gap-2'):
                    for request in pending_requests:
                        with ui.element('div').classes('card'):
                            with ui.element('div').classes('card-body'):
                                with ui.row().classes('items-center justify-between w-full'):
                                    with ui.column().classes('gap-1'):
                                        ui.label(request.name).classes('font-bold')
                                        if request.description:
                                            ui.label(request.description).classes('text-sm text-secondary')
                                        ui.label(f'Requested: {request.requested_at.strftime("%Y-%m-%d %H:%M")}').classes('text-xs text-secondary')
                                    with ui.element('span').classes('badge badge-warning'):
                                        ui.label('Pending Review')

        with Card.create(title='My Organizations'):
            # Add request button at the top
            async def request_organization():
                await self._show_request_dialog()

            ui.button(
                'Request New Organization',
                icon='add_business',
                on_click=request_organization
            ).classes('btn mb-4').props('color=primary')

            if not memberships:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('business').classes('text-secondary icon-large')
                    ui.label('Not a member of any organizations').classes('text-secondary')
                    ui.label('Request a new organization or wait for an invitation').classes('text-secondary text-sm')
            else:
                def render_name(m):
                    return ui.label(m.organization.name).classes('font-bold')

                def render_description(m):
                    return ui.label(m.organization.description or 'No description').classes('text-secondary')

                async def render_permissions(m):
                    perms = await m.permissions.all()
                    if perms:
                        perm_names = [p.permission_name for p in perms]
                        with ui.element('div').classes('flex gap-1 flex-wrap'):
                            for name in perm_names:
                                ui.element('span').classes('badge badge-info').text = name
                    else:
                        ui.label('Member').classes('text-secondary')

                async def render_actions(m):
                    with ui.row().classes('gap-2'):
                        # Show admin button if user can access the organization admin panel
                        # (superadmins or organization admins)
                        can_admin = await self.service.user_can_admin_org(self.user, m.organization.id)
                        if can_admin:
                            ui.button('Admin Panel', icon='admin_panel_settings',
                                    on_click=lambda org=m.organization: ui.navigate.to(f'/orgs/{org.id}/admin')).classes('btn')

                        ui.button('Leave', icon='exit_to_app',
                                on_click=lambda org=m.organization: self._leave_organization(org.id, org.name)).props('color=warning').classes('btn')

                columns = [
                    TableColumn('Organization', cell_render=render_name),
                    TableColumn('Description', cell_render=render_description),
                    TableColumn('Your Permissions', cell_render=render_permissions),
                    TableColumn('Actions', cell_render=render_actions),
                ]
                table = ResponsiveTable(columns, memberships)
                await table.render()

    async def _show_request_dialog(self) -> None:
        """Show dialog to request a new organization."""
        with ui.dialog() as request_dialog:
            with ui.element('div').classes('card dialog-card'):
                # Header
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('add_business').classes('icon-medium')
                            ui.label('Request New Organization').classes('text-xl text-bold')
                        ui.button(icon='close', on_click=request_dialog.close).props('flat round dense')

                # Body
                with ui.element('div').classes('card-body'):
                    with ui.column().classes('gap-4 w-full'):
                        ui.label('Submit a request to create a new organization. A SUPERADMIN will review your request.').classes('text-sm text-secondary')

                        # Input fields
                        name_input = ui.input(
                            label='Organization Name',
                            placeholder='Enter organization name'
                        ).classes('w-full').props('outlined')

                        description_input = ui.textarea(
                            label='Description',
                            placeholder='Describe the purpose of this organization'
                        ).classes('w-full').props('outlined rows=4')

                        # Action buttons
                        with ui.row().classes('justify-end gap-2 mt-4'):
                            ui.button('Cancel', on_click=request_dialog.close).classes('btn')

                            async def submit_request():
                                if not name_input.value or not name_input.value.strip():
                                    ui.notify('Organization name is required', type='warning')
                                    return

                                try:
                                    # Create the request
                                    await OrganizationRequest.create(
                                        name=name_input.value.strip(),
                                        description=description_input.value.strip() if description_input.value else None,
                                        requested_by=self.user,
                                        status=OrganizationRequest.RequestStatus.PENDING
                                    )

                                    ui.notify('Organization request submitted successfully. A SUPERADMIN will review it.', type='positive')
                                    request_dialog.close()
                                    await self._refresh()

                                except Exception as e:
                                    logger.error("Failed to create organization request: %s", e, exc_info=True)
                                    ui.notify(f'Failed to submit request: {str(e)}', type='negative')

                            ui.button('Submit Request', on_click=submit_request).classes('btn').props('color=positive')

        request_dialog.open()

    async def render(self) -> None:
        """Render the organizations view."""
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
