"""
Discord Server Management View.

View for linking and managing Discord servers connected to an organization.
"""

from __future__ import annotations
from nicegui import ui
from models import User
from models.organizations import Organization
from components.card import Card
from components.dialogs.common import ConfirmDialog
from application.services.discord_guild_service import DiscordGuildService
from application.services.organization_service import OrganizationService
import logging

logger = logging.getLogger(__name__)


class DiscordServersView:
    """View for managing Discord servers linked to an organization."""

    def __init__(self, user: User, organization: Organization):
        self.user = user
        self.organization = organization
        self.service = DiscordGuildService()
        self.org_service = OrganizationService()
        self.can_manage = False
        self.container = None

    async def render(self):
        """Render the Discord servers view."""
        # Check management permissions
        self.can_manage = await self.org_service.user_can_admin_org(
            self.user,
            self.organization.id
        )

        with Card.create(title='Discord Servers'):
            ui.label(
                'Link Discord servers to your organization to enable bot features.'
            ).classes('text-secondary mb-3')

            # Add server button (for admins/owners)
            if self.can_manage:
                ui.button(
                    'Add Discord Server',
                    icon='add',
                    on_click=self._add_server
                ).classes('btn-primary mb-3')

            # Container for server list
            self.container = ui.element('div')
            await self._refresh_servers()

    async def _refresh_servers(self):
        """Refresh the server list display."""
        if not self.container:
            return

        self.container.clear()

        with self.container:
            # Get linked servers
            guilds = await self.service.list_guilds(self.user, self.organization.id)

            if not guilds:
                with ui.element('div').classes('text-center mt-4'):
                    ui.icon('dns').classes('text-secondary icon-large')
                    ui.label('No Discord servers linked yet').classes('text-secondary')
                return

            # Render each server
            with ui.element('div').classes('flex flex-col gap-3'):
                for guild in guilds:
                    await self._render_server(guild)

    async def _render_server(self, guild):
        """Render a single Discord server card."""
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-body flex justify-between items-center'):
                # Server info
                with ui.element('div').classes('flex items-center gap-3'):
                    # Server icon
                    if guild.guild_icon_url:
                        ui.image(guild.guild_icon_url).classes('w-12 h-12 rounded')
                    else:
                        with ui.element('div').classes('w-12 h-12 rounded bg-secondary flex items-center justify-center'):
                            ui.icon('dns').classes('text-white')

                    # Server details
                    with ui.element('div'):
                        ui.label(guild.guild_name).classes('font-bold text-lg')
                        with ui.element('div').classes('text-sm text-secondary'):
                            await guild.fetch_related('linked_by')
                            ui.label(f'Linked by {guild.linked_by.discord_username}')
                            if guild.verified_admin:
                                ui.icon('verified').classes('text-success ml-2').tooltip('Admin verified')

                # Actions
                if self.can_manage:
                    with ui.element('div'):
                        ui.button(
                            icon='delete',
                            on_click=lambda g=guild: self._confirm_unlink(g)
                        ).classes('btn-sm text-danger').props('flat').tooltip('Unlink Server')

    async def _add_server(self):
        """Start the Discord server linking process."""
        # Use the service directly instead of API call
        from config import settings

        base_url = settings.BASE_URL or "http://localhost:8080"
        redirect_uri = f"{base_url}/discord-guild/callback"

        # Generate invite URL using service
        invite_url = self.service.generate_bot_invite_url(
            self.organization.id,
            redirect_uri
        )

        # Open Discord invite in new tab using WindowUtils
        ui.run_javascript(f'window.WindowUtils.open("{invite_url}");')
        ui.notify(
            'Opening Discord... Select a server and grant permissions. You will be redirected back after installation.',
            type='info',
            timeout=5000
        )

    async def _confirm_unlink(self, guild):
        """Confirm and unlink a Discord server."""
        async def do_unlink():
            success = await self.service.unlink_guild(
                self.user,
                self.organization.id,
                guild.id
            )
            if success:
                ui.notify('Discord server unlinked successfully', type='positive')
                await self._refresh_servers()
            else:
                ui.notify('Failed to unlink server', type='negative')

        dialog = ConfirmDialog(
            title=f'Unlink Discord Server: {guild.guild_name}?',
            message='The bot will no longer be able to operate in this server for your organization.',
            on_confirm=do_unlink
        )
        await dialog.show()
