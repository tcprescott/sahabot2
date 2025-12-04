"""
Tournament-specific admin pages.

Accessible by tournament managers and organization admins.
Provides detailed tournament management with dedicated pages for different aspects.
"""

from nicegui import ui
from components.base_page import BasePage
from application.services.organizations.organization_service import OrganizationService
from modules.tournament.repositories.tournament_repository import TournamentRepository
from modules.tournament.views.admin import (
    TournamentDiscordEventsView,
    TournamentOverviewView,
    TournamentPlayersView,
    TournamentPresetSelectionRulesView,
    TournamentRacetimeSettingsView,
    TournamentRandomizerSettingsView,
    TournamentSettingsView,
)


def _create_tournament_sidebar(base: BasePage, org_id: int, tournament_id: int, active: str):
    """Create common sidebar for tournament admin pages."""
    sidebar_items = [
        base.create_nav_link(
            "Back to Organization",
            "arrow_back",
            f"/orgs/{org_id}/admin/tournaments",
        ),
        base.create_separator(),
        base.create_nav_link("Overview", "dashboard", f"/org/{org_id}/tournament/{tournament_id}/admin", active=(active == "overview")),
        base.create_nav_link("Players", "people", f"/org/{org_id}/tournament/{tournament_id}/admin/players", active=(active == "players")),
        base.create_nav_link("RaceTime Settings", "settings", f"/org/{org_id}/tournament/{tournament_id}/admin/racetime", active=(active == "racetime")),
        base.create_nav_link("Discord Events", "event_available", f"/org/{org_id}/tournament/{tournament_id}/admin/discord-events", active=(active == "discord-events")),
        base.create_nav_link("Randomizer Settings", "casino", f"/org/{org_id}/tournament/{tournament_id}/admin/randomizer-settings", active=(active == "randomizer-settings")),
        base.create_nav_link("Preset Selection Rules", "rule", f"/org/{org_id}/tournament/{tournament_id}/admin/preset-rules", active=(active == "preset-rules")),
        base.create_nav_link("Settings", "tune", f"/org/{org_id}/tournament/{tournament_id}/admin/settings", active=(active == "settings")),
    ]
    return sidebar_items


async def _get_tournament_context(organization_id: int, tournament_id: int):
    """Get organization and tournament, checking permissions."""
    from middleware.auth import DiscordAuthService
    
    user = await DiscordAuthService.get_current_user()
    org_service = OrganizationService()
    
    # Check authorization
    can_manage = await org_service.user_can_manage_tournaments(user, organization_id)
    if not can_manage:
        return None, None, None, "You do not have permission to manage tournaments"
    
    # Get organization
    org = await org_service.get_organization(organization_id)
    if not org:
        return None, None, None, "Organization not found"
    
    # Get tournament
    tournament_repo = TournamentRepository()
    tournament = await tournament_repo.get_for_org(organization_id, tournament_id)
    if not tournament:
        return None, None, None, "Tournament not found"
    
    return user, org, tournament, None


def register():
    """Register tournament admin page routes."""

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin")
    async def tournament_overview_page(organization_id: int, tournament_id: int):
        """Tournament administration overview page."""
        base = BasePage.authenticated_page(title="Tournament Admin")

        async def content(page: BasePage):
            """Render tournament overview content."""
            user, org, tournament, error = await _get_tournament_context(organization_id, tournament_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")
            
            view = TournamentOverviewView(user, org, tournament)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, tournament_id, "overview")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin/players")
    async def tournament_players_page(organization_id: int, tournament_id: int):
        """Tournament players page."""
        base = BasePage.authenticated_page(title="Tournament Players")

        async def content(page: BasePage):
            """Render tournament players content."""
            user, org, tournament, error = await _get_tournament_context(organization_id, tournament_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")
            
            view = TournamentPlayersView(user, org, tournament)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, tournament_id, "players")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin/racetime")
    async def tournament_racetime_page(organization_id: int, tournament_id: int):
        """Tournament RaceTime settings page."""
        base = BasePage.authenticated_page(title="RaceTime Settings")

        async def content(page: BasePage):
            """Render RaceTime settings content."""
            user, org, tournament, error = await _get_tournament_context(organization_id, tournament_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")
            
            view = TournamentRacetimeSettingsView(user, org, tournament)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, tournament_id, "racetime")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin/discord-events")
    async def tournament_discord_events_page(organization_id: int, tournament_id: int):
        """Tournament Discord events page."""
        base = BasePage.authenticated_page(title="Discord Events")

        async def content(page: BasePage):
            """Render Discord events content."""
            user, org, tournament, error = await _get_tournament_context(organization_id, tournament_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")
            
            view = TournamentDiscordEventsView(user, org, tournament)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, tournament_id, "discord-events")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin/randomizer-settings")
    async def tournament_randomizer_settings_page(organization_id: int, tournament_id: int):
        """Tournament randomizer settings page."""
        base = BasePage.authenticated_page(title="Randomizer Settings")

        async def content(page: BasePage):
            """Render randomizer settings content."""
            user, org, tournament, error = await _get_tournament_context(organization_id, tournament_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")
            
            view = TournamentRandomizerSettingsView(user, org, tournament)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, tournament_id, "randomizer-settings")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin/preset-rules")
    async def tournament_preset_rules_page(organization_id: int, tournament_id: int):
        """Tournament preset selection rules page."""
        base = BasePage.authenticated_page(title="Preset Selection Rules")

        async def content(page: BasePage):
            """Render preset selection rules content."""
            user, org, tournament, error = await _get_tournament_context(organization_id, tournament_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")
            
            view = TournamentPresetSelectionRulesView(user, org, tournament)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, tournament_id, "preset-rules")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin/settings")
    async def tournament_settings_page(organization_id: int, tournament_id: int):
        """Tournament settings page."""
        base = BasePage.authenticated_page(title="Tournament Settings")

        async def content(page: BasePage):
            """Render tournament settings content."""
            user, org, tournament, error = await _get_tournament_context(organization_id, tournament_id)
            
            if error:
                ui.notify(error, color="negative")
                ui.navigate.to(f"/org/{organization_id}")
                return
            
            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")
            
            view = TournamentSettingsView(user, org, tournament)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, tournament_id, "settings")
        await base.render(content, sidebar_items)
