"""
Organization Members view.

List organization members and manage their permissions.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime
from nicegui import ui
from models import Organization
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from components.dialogs import (
    MemberPermissionsDialog,
    InviteMemberDialog,
    OrganizationInviteDialog,
    ConfirmDialog,
)
from application.services.organization_service import OrganizationService
from application.services.authorization_service import AuthorizationService
from application.services.organization_invite_service import OrganizationInviteService
from config import settings


class OrganizationMembersView:
    """Manage organization members and their permissions."""

    def __init__(self, organization: Organization, user: Any) -> None:
        self.organization = organization
        self.user = user
        self.service = OrganizationService()
        self.auth_service = AuthorizationService()
        self.invite_service = OrganizationInviteService()
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

    async def _render_invite_links(self) -> None:
        """Render invite links management section."""
        invites = await self.invite_service.list_org_invites(self.user, self.organization.id)

        with Card.create(title='Invite Links'):
            with ui.row().classes('w-full justify-between mb-2'):
                ui.label('Share these links to let users join the organization')
                if self.can_manage:
                    async def open_create_dialog():
                        await self._open_create_invite_dialog()
                    ui.button('Create Invite Link', icon='add_link', on_click=open_create_dialog).props('color=positive').classes('btn')

            if not invites:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('link').classes('text-secondary icon-large')
                    ui.label('No invite links yet').classes('text-secondary')
                    ui.label('Create a link to share with new members').classes('text-secondary text-sm')
            else:
                def render_invite_url(inv):
                    full_url = f'{settings.BASE_URL}/invite/{inv.slug}'
                    with ui.row().classes('items-center gap-2'):
                        ui.label(full_url).classes('font-mono text-sm')
                        async def copy_to_clipboard():
                            # Use JavaScript to copy to clipboard
                            await ui.run_javascript(f'''
                                navigator.clipboard.writeText("{full_url}").then(() => {{
                                    console.log("Copied to clipboard: {full_url}");
                                }}).catch(err => {{
                                    console.error("Failed to copy: ", err);
                                }});
                            ''')
                            ui.notify('Link copied to clipboard!', type='positive')
                        ui.button(icon='content_copy', on_click=copy_to_clipboard).props('flat dense')

                def render_status(inv):
                    if not inv.is_active:
                        ui.label('Inactive').classes('badge badge-secondary')
                    elif inv.expires_at and inv.expires_at < datetime.now():
                        ui.label('Expired').classes('badge badge-danger')
                    elif inv.max_uses and inv.uses_count >= inv.max_uses:
                        ui.label('Max uses reached').classes('badge badge-warning')
                    else:
                        ui.label('Active').classes('badge badge-success')

                def render_uses(inv):
                    if inv.max_uses:
                        ui.label(f'{inv.uses_count} / {inv.max_uses}')
                    else:
                        ui.label(f'{inv.uses_count} / ∞')

                def render_invite_actions(inv):
                    with ui.element('div').classes('flex gap-2'):
                        if self.can_manage:
                            if inv.is_active:
                                async def deactivate():
                                    await self.invite_service.update_invite(self.user, self.organization.id, inv.id, is_active=False)
                                    await self._refresh()
                                ui.button('Deactivate', icon='link_off', on_click=deactivate).classes('btn')
                            else:
                                async def activate():
                                    await self.invite_service.update_invite(self.user, self.organization.id, inv.id, is_active=True)
                                    await self._refresh()
                                ui.button('Activate', icon='link', on_click=activate).classes('btn')
                            
                            async def delete_invite():
                                async def do_delete():
                                    await self.invite_service.delete_invite(self.user, self.organization.id, inv.id)
                                    await self._refresh()
                                dialog = ConfirmDialog(
                                    title='Delete Invite Link',
                                    message=f"Are you sure you want to delete the invite link '/invite/{inv.slug}'?",
                                    on_confirm=do_delete
                                )
                                await dialog.show()
                            ui.button('Delete', icon='delete', on_click=delete_invite).classes('btn').props('color=negative')

                def render_created(invite):
                    DateTimeLabel.datetime(invite.created_at)

                columns = [
                    TableColumn('Invite URL', cell_render=render_invite_url),
                    TableColumn('Status', cell_render=render_status),
                    TableColumn('Uses', cell_render=render_uses),
                    TableColumn('Created', cell_render=render_created),
                    TableColumn('Actions', cell_render=render_invite_actions),
                ]
                table = ResponsiveTable(columns, invites)
                await table.render()

    async def _open_create_invite_dialog(self) -> None:
        """Open dialog to create an invite link."""
        async def on_submit(slug, max_uses, expires_at):
            _invite, error = await self.invite_service.create_invite(
                self.user,
                self.organization.id,
                slug,
                max_uses,
                expires_at
            )
            if error:
                ui.notify(error, type='negative')
            else:
                ui.notify('Invite link created successfully!', type='positive')
                await self._refresh()

        dialog = OrganizationInviteDialog(on_submit=on_submit)
        await dialog.show()

    async def _render_content(self) -> None:
        """Render the members list and controls."""
        # Render invite links first
        await self._render_invite_links()

        # Then render members list
        members = await self.service.list_members(self.organization.id)

        with Card.create(title='Organization Members', classes='mt-2'):
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

                def render_joined(m):
                    DateTimeLabel.datetime(m.joined_at)

                columns = [
                    TableColumn('Username', cell_render=render_username),
                    TableColumn('Permissions', cell_render=render_permissions),
                    TableColumn('Joined', cell_render=render_joined),
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
