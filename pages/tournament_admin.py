"""
Tournament-specific admin page.

Accessible by tournament managers and organization admins.
Provides detailed tournament management with dedicated views for different aspects.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organizations.organization_service import OrganizationService
from application.repositories.tournament_repository import TournamentRepository
from views.tournament_admin import (
    TournamentOverviewView,
    TournamentPlayersView,
    TournamentRacetimeSettingsView,
    TournamentRacetimeChatCommandsView,
    TournamentDiscordEventsView,
    TournamentSettingsView,
)
from views.tournaments import TournamentManagementView


def register():
    """Register tournament admin page routes."""

    @ui.page('/org/{organization_id}/tournament/{tournament_id}/admin')
    async def tournament_admin_page(organization_id: int, tournament_id: int):
        """Tournament administration page."""
        base = BasePage.authenticated_page(title='Tournament Admin')
        org_service = OrganizationService()

        # Pre-check authorization
        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()
        can_manage = await org_service.user_can_manage_tournaments(user, organization_id)

        async def content(page: BasePage):
            """Render tournament admin content."""
            # Re-check authorization inside content
            if not can_manage:
                ui.notify('You do not have permission to manage tournaments', color='negative')
                ui.navigate.to(f'/org/{organization_id}')
                return

            # Get organization
            org = await org_service.get_organization(organization_id)
            if not org:
                ui.label('Organization not found').classes('text-negative')
                return

            # Get tournament
            tournament_repo = TournamentRepository()
            tournament = await tournament_repo.get_for_org(organization_id, tournament_id)
            if not tournament:
                ui.label('Tournament not found').classes('text-negative')
                return

            # Tournament header
            with ui.element('div').classes('card mb-4'):
                with ui.element('div').classes('card-header'):
                    with ui.row().classes('items-center justify-between w-full'):
                        ui.label(tournament.name).classes('text-2xl font-bold')

            # Register content loaders for different sections
            async def load_overview():
                """Load tournament overview."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentOverviewView(page.user, org, tournament)
                        await view.render()

            async def load_players():
                """Load tournament players."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentPlayersView(page.user, org, tournament)
                        await view.render()

            async def load_racetime():
                """Load RaceTime settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentRacetimeSettingsView(page.user, org, tournament)
                        await view.render()

            async def load_discord_events():
                """Load Discord events settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentDiscordEventsView(page.user, org, tournament)
                        await view.render()

            async def load_chat_commands():
                """Load chat commands."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentRacetimeChatCommandsView(page.user, org, tournament)
                        await view.render()

            async def load_settings():
                """Load tournament settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentSettingsView(page.user, org, tournament)
                        await view.render()

            async def load_management():
                """Load tournament management (registrations)."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        view = TournamentManagementView(org, page.user)
                        view.selected_tournaments = [tournament_id]
                        await view.render()

            # Register loaders
            page.register_content_loader('overview', load_overview)
            page.register_content_loader('players', load_players)
            page.register_content_loader('racetime', load_racetime)
            page.register_content_loader('discord-events', load_discord_events)
            page.register_content_loader('chat-commands', load_chat_commands)
            page.register_content_loader('settings', load_settings)
            page.register_content_loader('management', load_management)

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await load_overview()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Back to Organization', 'arrow_back', f'/orgs/{organization_id}/admin?view=tournaments'),
            base.create_separator(),
            base.create_sidebar_item_with_loader('Overview', 'dashboard', 'overview'),
            base.create_sidebar_item_with_loader('Players', 'people', 'players'),
            base.create_sidebar_item_with_loader('Registrations', 'how_to_reg', 'management'),
            base.create_sidebar_item_with_loader('RaceTime Settings', 'settings', 'racetime'),
            base.create_sidebar_item_with_loader('Discord Events', 'event_available', 'discord-events'),
            base.create_sidebar_item_with_loader('Chat Commands', 'chat', 'chat-commands'),
            base.create_sidebar_item_with_loader('Settings', 'tune', 'settings'),
        ]

        await base.render(content, sidebar_items, use_dynamic_content=True)

