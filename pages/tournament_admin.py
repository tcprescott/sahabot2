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
    TournamentDiscordEventsView,
    TournamentSettingsView,
    TournamentRandomizerSettingsView,
    TournamentPresetSelectionRulesView,
)


def register():
    """Register tournament admin page routes."""

    @ui.page("/org/{organization_id}/tournament/{tournament_id}/admin")
    async def tournament_admin_page(organization_id: int, tournament_id: int):
        """Tournament administration page."""
        base = BasePage.authenticated_page(title="Tournament Admin")
        org_service = OrganizationService()

        # Pre-check authorization
        from middleware.auth import DiscordAuthService

        user = await DiscordAuthService.get_current_user()
        can_manage = await org_service.user_can_manage_tournaments(
            user, organization_id
        )

        async def content(page: BasePage):
            """Render tournament admin content."""
            # Re-check authorization inside content
            if not can_manage:
                ui.notify(
                    "You do not have permission to manage tournaments", color="negative"
                )
                ui.navigate.to(f"/org/{organization_id}")
                return

            # Get organization
            org = await org_service.get_organization(organization_id)
            if not org:
                ui.label("Organization not found").classes("text-negative")
                return

            # Get tournament
            tournament_repo = TournamentRepository()
            tournament = await tournament_repo.get_for_org(
                organization_id, tournament_id
            )
            if not tournament:
                ui.label("Tournament not found").classes("text-negative")
                return

            # Tournament header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(tournament.name).classes("text-2xl font-bold")

            # Register content loaders for different sections
            async def load_overview():
                """Load tournament overview."""
                view = TournamentOverviewView(page.user, org, tournament)
                await page.load_view_into_container(view)

            async def load_players():
                """Load tournament players."""
                view = TournamentPlayersView(page.user, org, tournament)
                await page.load_view_into_container(view)

            async def load_racetime():
                """Load RaceTime settings."""
                view = TournamentRacetimeSettingsView(page.user, org, tournament)
                await page.load_view_into_container(view)

            async def load_discord_events():
                """Load Discord events settings."""
                view = TournamentDiscordEventsView(page.user, org, tournament)
                await page.load_view_into_container(view)

            async def load_settings():
                """Load tournament settings."""
                view = TournamentSettingsView(page.user, org, tournament)
                await page.load_view_into_container(view)

            async def load_randomizer_settings():
                """Load randomizer settings."""
                view = TournamentRandomizerSettingsView(page.user, org, tournament)
                await page.load_view_into_container(view)

            async def load_preset_rules():
                """Load preset selection rules."""
                view = TournamentPresetSelectionRulesView(page.user, org, tournament)
                await page.load_view_into_container(view)

            # Register loaders
            page.register_content_loader("overview", load_overview)
            page.register_content_loader("players", load_players)
            page.register_content_loader("racetime", load_racetime)
            page.register_content_loader("discord-events", load_discord_events)
            page.register_content_loader(
                "randomizer-settings", load_randomizer_settings
            )
            page.register_content_loader("preset-rules", load_preset_rules)
            page.register_content_loader("settings", load_settings)

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await load_overview()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link(
                "Back to Organization",
                "arrow_back",
                f"/orgs/{organization_id}/admin?view=tournaments",
            ),
            base.create_separator(),
        ]
        sidebar_items.extend(base.create_sidebar_items([
            ("Overview", "dashboard", "overview"),
            ("Players", "people", "players"),
            ("RaceTime Settings", "settings", "racetime"),
            ("Discord Events", "event_available", "discord-events"),
            ("Randomizer Settings", "casino", "randomizer-settings"),
            ("Preset Selection Rules", "rule", "preset-rules"),
            ("Settings", "tune", "settings"),
        ]))

        await base.render(content, sidebar_items, use_dynamic_content=True)
