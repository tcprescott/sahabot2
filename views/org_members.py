"""
Organization Members view.

List organization members and manage their permissions.
"""

from __future__ import annotations
from typing import Any
from nicegui import ui
from models import Organization
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.dialogs.member_permissions_dialog import MemberPermissionsDialog
from components.dialogs.invite_member_dialog import InviteMemberDialog
from application.services.organization_service import OrganizationService
from application.services.authorization_service import AuthorizationService


class OrganizationMembersView:
    """Manage organization members and their permissions."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user
        self.service = OrganizationService()
        self.auth_service = AuthorizationService()
        self.container = None
        self.can_manage = False  # Will be set in render

    async def _refresh(self) -> None:
        """Refresh the members list."""
        if self.container:
            self.container.clear()
            with self.container:
                await self._render_content()

    async def _open_invite_dialog(self) -> None:
        """Open dialog to invite a member."""
        dialog = InviteMemberDialog(
            organization_id=self.organization.id,
            organization_name=self.organization.name,
            on_save=self._refresh
        )
        await dialog.show()

    async def _open_permissions_dialog(self, member) -> None:
        """Open dialog to edit a member's permissions."""
        # Get current permissions
        current_perms = await self.service.list_member_permissions(self.organization.id, member.user_id)
        # Get available types
        available_types = self.service.list_available_permission_types()

        dialog = MemberPermissionsDialog(
            organization_id=self.organization.id,
            user_id=member.user_id,
            username=member.user.discord_username if hasattr(member, 'user') and member.user else f"User {member.user_id}",
            current_permissions=current_perms,
            available_types=available_types,
            on_save=self._refresh
        )
        await dialog.show()

    async def _render_content(self) -> None:
        """Render the members list and controls."""
        members = await self.service.list_members(self.organization.id)

        with Card.create(title='Organization Members'):
            with ui.row().classes('w-full justify-between mb-2'):
                ui.label(f'{len(members)} member(s) in this organization')
                if self.can_manage:
                    ui.button('Invite Member', icon='person_add', on_click=self._open_invite_dialog).props('color=positive').classes('btn')

            if not members:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('people').classes('text-secondary icon-large')
                    ui.label('No members yet').classes('text-secondary')
                    ui.label('Add members to get started').classes('text-secondary text-sm')
            else:
                def render_username(m):
                    if hasattr(m, 'user') and m.user:
                        return ui.label(m.user.discord_username)
                    return ui.label(f'User {m.user_id}')

                async def render_permissions(m):
                    perms = await m.permissions.all() if hasattr(m, 'permissions') else []
                    if perms:
                        perm_names = [p.permission_name for p in perms]
                        with ui.element('div').classes('flex gap-1 flex-wrap'):
                            for name in perm_names:
                                ui.element('span').classes('badge badge-info').text = name
                    else:
                        ui.label('No permissions').classes('text-secondary')

                def render_actions(m):
                    with ui.element('div').classes('flex gap-2'):
                        if self.can_manage:
                            ui.button('Edit Permissions', icon='security', on_click=lambda m=m: self._open_permissions_dialog(m)).classes('btn')
                        else:
                            ui.label('—').classes('text-secondary')

                columns = [
                    TableColumn('Username', cell_render=render_username),
                    TableColumn('Permissions', cell_render=render_permissions),
                    TableColumn('Joined', key='joined_at'),
                    TableColumn('Actions', cell_render=render_actions),
                ]
                table = ResponsiveTable(columns, members)
                await table.render()

    async def render(self) -> None:
        """Render the members view."""
        # Check if user can manage members
        self.can_manage = await self.auth_service.can_manage_org_members(self.user, self.organization.id)
        
        self.container = ui.column().classes('full-width')
        with self.container:
            await self._render_content()
