"""
Organization-specific admin page.

Accessible by SUPERADMIN/ADMIN or members with an org-level admin role.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organization_service import OrganizationService
from views.organization import (
    OrganizationOverviewView,
    OrganizationMembersView,
    OrganizationPermissionsView,
    OrganizationSettingsView,
    OrganizationTournamentsView,
    OrganizationAsyncTournamentsView,
    OrganizationStreamChannelsView,
    OrganizationScheduledTasksView,
    DiscordServersView,
)


def register():
    """Register organization admin route."""

    @ui.page('/orgs/{organization_id}/admin')
    async def organization_admin_page(organization_id: int):
        """Organization admin page with scoped authorization checks."""
        base = BasePage.authenticated_page(title="Organization Admin")
        service = OrganizationService()

        # Pre-check authorization to determine sidebar structure
        # We need to do this outside content() so we can build sidebar_items
        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()
        
        allowed_admin = await service.user_can_admin_org(user, organization_id)
        allowed_tournaments = await service.user_can_manage_tournaments(user, organization_id)
        allowed = allowed_admin or allowed_tournaments

        async def content(page: BasePage):
            # Re-check authorization inside content
            if not allowed:
                ui.notify('You do not have access to administer this organization.', color='negative')
                ui.navigate.to(f'/org/{organization_id}')
                return

            org = await service.get_organization(organization_id)
            if not org:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-header'):
                        ui.label('Organization not found')
                    with ui.element('div').classes('card-body'):
                        ui.button('Back to Organizations', on_click=lambda: ui.navigate.to('/?view=organizations')).classes('btn')
                return

            # Register content loaders for different sections
            async def load_overview():
                """Load organization overview."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationOverviewView(org, page.user)
                        await view.render()

            async def load_members():
                """Load members management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationMembersView(org, page.user)
                        await view.render()

            async def load_permissions():
                """Load permissions management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationPermissionsView(org, page.user)
                        await view.render()

            async def load_settings():
                """Load organization settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationSettingsView(org, page.user)
                        await view.render()

            async def load_tournaments():
                """Load organization tournaments management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationTournamentsView(org, page.user)
                        await view.render()

            async def load_async_tournaments():
                """Load organization async tournaments management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationAsyncTournamentsView(org, page.user)
                        await view.render()

            async def load_stream_channels():
                """Load organization stream channels management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationStreamChannelsView(org, page.user)
                        await view.render()

            async def load_scheduled_tasks():
                """Load organization scheduled tasks management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = OrganizationScheduledTasksView(org, page.user)
                        await view.render()

            async def load_discord_servers():
                """Load Discord servers management."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = DiscordServersView(page.user, org)
                        await view.render()

            # Register loaders (restrict for non-admin tournament managers)
            if allowed_admin:
                page.register_content_loader('overview', load_overview)
                page.register_content_loader('members', load_members)
                page.register_content_loader('permissions', load_permissions)
                page.register_content_loader('stream_channels', load_stream_channels)
                page.register_content_loader('scheduled_tasks', load_scheduled_tasks)
                page.register_content_loader('discord_servers', load_discord_servers)
                page.register_content_loader('settings', load_settings)
            # Tournaments accessible to admins and TOURNAMENT_MANAGERs
            page.register_content_loader('tournaments', load_tournaments)
            page.register_content_loader('async_tournaments', load_async_tournaments)

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                # Load default view: overview for admins, tournaments for managers
                if allowed_admin:
                    await load_overview()
                else:
                    await load_tournaments()

        # Create sidebar items (conditionally for non-admins)
        sidebar_items = [
            base.create_nav_link('Back to Organization', 'arrow_back', f'/org/{organization_id}'),
            base.create_separator(),
        ]

        if allowed_admin:
            sidebar_items.extend([
                base.create_sidebar_item_with_loader('Overview', 'dashboard', 'overview'),
                base.create_sidebar_item_with_loader('Members', 'people', 'members'),
                base.create_sidebar_item_with_loader('Permissions', 'verified_user', 'permissions'),
                base.create_sidebar_item_with_loader('Stream Channels', 'cast', 'stream_channels'),
                base.create_sidebar_item_with_loader('Tournaments', 'emoji_events', 'tournaments'),
                base.create_sidebar_item_with_loader('Async Tournaments', 'schedule', 'async_tournaments'),
                base.create_sidebar_item_with_loader('Discord Servers', 'dns', 'discord_servers'),
                base.create_sidebar_item_with_loader('Scheduled Tasks', 'schedule', 'scheduled_tasks'),
                base.create_sidebar_item_with_loader('Settings', 'settings', 'settings'),
            ])
        else:
            # Tournament managers see both regular and async tournaments
            sidebar_items.extend([
                base.create_sidebar_item_with_loader('Tournaments', 'emoji_events', 'tournaments'),
                base.create_sidebar_item_with_loader('Async Tournaments', 'schedule', 'async_tournaments'),
            ])

        await base.render(content, sidebar_items, use_dynamic_content=True)
