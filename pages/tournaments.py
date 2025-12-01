"""
Tournaments page.

Shows organization selector, then organization-scoped tournament views.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organizations.organization_service import OrganizationService
from application.services.tournaments import TournamentService
from application.services.async_qualifiers.async_qualifier_service import (
    AsyncQualifierService,
)
from application.services.tournaments import (
    TournamentUsageService,
)
from views.tournaments import (
    EventScheduleView,
    MyMatchesView,
    MySettingsView,
)
from views.organization import (
    OrganizationOverviewView,
)


def _create_org_sidebar(base: BasePage, org_id: int, can_admin: bool, active_tournaments, active_async_tournaments):
    """Create common sidebar for organization pages."""
    sidebar_items = [
        base.create_nav_link("Back to Organizations", "arrow_back", "/?view=organizations"),
        base.create_separator(),
        base.create_nav_link("Overview", "dashboard", f"/org/{org_id}"),
        base.create_nav_link("Tournaments", "emoji_events", f"/org/{org_id}/tournament"),
        base.create_nav_link("Async Qualifiers", "schedule", f"/org/{org_id}/async"),
    ]

    # Add admin link if user has permissions
    if can_admin:
        sidebar_items.append(base.create_separator())
        sidebar_items.append(
            base.create_nav_link(
                "Administration",
                "admin_panel_settings",
                f"/orgs/{org_id}/admin",
            )
        )

    # Add active tournament links if there are any
    if active_tournaments or active_async_tournaments:
        sidebar_items.append(base.create_separator())

        # Add regular tournaments
        for tournament in active_tournaments:
            sidebar_items.append(
                base.create_nav_link(
                    f"🏆 {tournament.name}",
                    "emoji_events",
                    f"/org/{org_id}/tournament?tournament_id={tournament.id}",
                )
            )

        # Add async qualifiers
        for tournament in active_async_tournaments:
            sidebar_items.append(
                base.create_nav_link(
                    f"🏁 {tournament.name}",
                    "schedule",
                    f"/org/{org_id}/async/{tournament.id}",
                )
            )

    return sidebar_items


def _create_tournament_sidebar(base: BasePage, org_id: int, active: str):
    """Create sidebar for tournament pages."""
    return [
        base.create_nav_link("Back to Organization", "arrow_back", f"/org/{org_id}"),
        base.create_separator(),
        base.create_nav_link("Event Schedule", "event", f"/org/{org_id}/tournament", active=(active == "event_schedule")),
        base.create_nav_link("My Matches", "sports_esports", f"/org/{org_id}/tournament/my-matches", active=(active == "my_matches")),
        base.create_nav_link("My Settings", "settings", f"/org/{org_id}/tournament/my-settings", active=(active == "my_settings")),
    ]


def register():
    """Register tournament page routes."""

    @ui.page("/org/{organization_id}")
    async def organization_page(organization_id: int):
        """Organization page - show organization features and members."""
        base = BasePage.authenticated_page(title="Organization")
        org_service = OrganizationService()
        async_tournament_service = AsyncQualifierService()

        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()

        # Check if user is a member of this organization
        is_member = await org_service.is_member(user, organization_id)

        if not is_member:
            ui.notify(
                "You must be a member of this organization to view organization features.",
                color="negative",
            )
            ui.navigate.to("/?view=organizations")
            return

        # Check if user can access admin panel
        can_admin = await org_service.user_can_admin_org(user, organization_id)
        can_manage_tournaments = await org_service.user_can_manage_tournaments(
            user, organization_id
        )
        can_access_admin = can_admin or can_manage_tournaments

        # Get active tournaments for sidebar (using service layer)
        active_async_tournaments = (
            await async_tournament_service.list_active_org_tournaments(
                user, organization_id
            )
        )
        tournament_service = TournamentService()
        active_tournaments = await tournament_service.list_active_org_tournaments(
            user, organization_id
        )

        async def content(page: BasePage):
            """Render organization overview."""
            org = await org_service.get_organization(organization_id)
            if not org:
                with ui.element("div").classes("card"):
                    with ui.element("div").classes("card-header"):
                        ui.label("Organization not found")
                    with ui.element("div").classes("card-body"):
                        ui.button(
                            "Back to Organizations",
                            on_click=lambda: ui.navigate.to("/?view=organizations"),
                        ).classes("btn")
                return

            view = OrganizationOverviewView(org, page.user)
            await view.render()

        sidebar_items = _create_org_sidebar(
            base, organization_id, can_access_admin, 
            active_tournaments, active_async_tournaments
        )
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament")
    async def tournament_event_schedule_page(
        organization_id: int, tournament_id: int | None = None
    ):
        """Tournament event schedule page."""
        base = BasePage.authenticated_page(title="Event Schedule")
        org_service = OrganizationService()
        tournament_service = TournamentService()
        usage_service = TournamentUsageService()

        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()

        # Check if user is a member of this organization
        is_member = await org_service.is_member(user, organization_id)

        if not is_member:
            ui.notify(
                "You must be a member of this organization to view organization features.",
                color="negative",
            )
            ui.navigate.to("/?view=organizations")
            return

        # Track tournament usage if tournament_id is provided
        if tournament_id:
            tournament = await tournament_service.get_tournament(
                user, organization_id, tournament_id
            )
            if tournament:
                org = await org_service.get_organization(organization_id)
                if org:
                    await usage_service.track_tournament_access(
                        user=user,
                        tournament=tournament,
                        organization_id=organization_id,
                        organization_name=org.name,
                    )

        async def content(page: BasePage):
            """Render event schedule."""
            org = await org_service.get_organization(organization_id)
            if not org:
                ui.notify("Organization not found", color="negative")
                ui.navigate.to("/?view=organizations")
                return

            view = EventScheduleView(org, page.user)
            if tournament_id:
                view.selected_tournaments = [tournament_id]
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, "event_schedule")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/my-matches")
    async def tournament_my_matches_page(
        organization_id: int, tournament_id: int | None = None
    ):
        """Tournament my matches page."""
        base = BasePage.authenticated_page(title="My Matches")
        org_service = OrganizationService()
        tournament_service = TournamentService()

        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()

        # Check if user is a member of this organization
        is_member = await org_service.is_member(user, organization_id)

        if not is_member:
            ui.notify(
                "You must be a member of this organization to view organization features.",
                color="negative",
            )
            ui.navigate.to("/?view=organizations")
            return

        async def content(page: BasePage):
            """Render my matches."""
            org = await org_service.get_organization(organization_id)
            if not org:
                ui.notify("Organization not found", color="negative")
                ui.navigate.to("/?view=organizations")
                return

            view = MyMatchesView(org, page.user)
            if tournament_id:
                view.selected_tournaments = [tournament_id]
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, "my_matches")
        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/tournament/my-settings")
    async def tournament_my_settings_page(organization_id: int):
        """Tournament my settings page."""
        base = BasePage.authenticated_page(title="My Settings")
        org_service = OrganizationService()
        tournament_service = TournamentService()

        from middleware.auth import DiscordAuthService
        user = await DiscordAuthService.get_current_user()

        # Check if user is a member of this organization
        is_member = await org_service.is_member(user, organization_id)

        if not is_member:
            ui.notify(
                "You must be a member of this organization to view organization features.",
                color="negative",
            )
            ui.navigate.to("/?view=organizations")
            return

        async def content(page: BasePage):
            """Render my settings."""
            org = await org_service.get_organization(organization_id)
            if not org:
                ui.notify("Organization not found", color="negative")
                ui.navigate.to("/?view=organizations")
                return

            view = MySettingsView(page.user, org, tournament_service)
            await view.render()

        sidebar_items = _create_tournament_sidebar(base, organization_id, "my_settings")
        await base.render(content, sidebar_items)
