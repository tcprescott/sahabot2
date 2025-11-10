"""
Tournaments page.

Shows organization selector, then organization-scoped tournament views.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organizations.organization_service import OrganizationService
from application.services.tournaments.tournament_service import TournamentService
from application.services.async_qualifiers.async_qualifier_service import (
    AsyncQualifierService,
)
from application.services.tournaments.tournament_usage_service import (
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


def register():
    """Register tournament page routes."""

    @ui.page("/org/{organization_id}")
    async def organization_page(organization_id: int):
        """Organization page - show organization features and members."""
        base = BasePage.authenticated_page(title="Organization")
        org_service = OrganizationService()
        tournament_service = TournamentService()
        async_tournament_service = AsyncQualifierService()

        # Pre-check that user is a member of the organization
        from middleware.auth import DiscordAuthService

        user = await DiscordAuthService.get_current_user()

        # Check if user is a member of this organization
        is_member = await org_service.is_member(user, organization_id)

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
        active_tournaments = await tournament_service.list_active_org_tournaments(
            user, organization_id
        )

        async def content(page: BasePage):
            # Re-check membership inside content
            if not is_member:
                ui.notify(
                    "You must be a member of this organization to view organization features.",
                    color="negative",
                )
                ui.navigate.to("/?view=organizations")
                return

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

            # Register content loaders for different sections
            async def load_overview():
                """Load overview view."""
                view = OrganizationOverviewView(org, page.user)
                await page.load_view_into_container(view)

            # Register loaders
            page.register_content_loader("overview", load_overview)

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await load_overview()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link(
                "Back to Organizations", "arrow_back", "/?view=organizations"
            ),
            base.create_separator(),
            base.create_sidebar_item_with_loader("Overview", "dashboard", "overview"),
            base.create_nav_link(
                "Tournaments", "emoji_events", f"/org/{organization_id}/tournament"
            ),
            base.create_nav_link(
                "Async Qualifiers", "schedule", f"/org/{organization_id}/async"
            ),
        ]

        # Add admin link if user has permissions
        if can_access_admin:
            sidebar_items.append(base.create_separator())
            sidebar_items.append(
                base.create_nav_link(
                    "Administration",
                    "admin_panel_settings",
                    f"/orgs/{organization_id}/admin",
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
                        f"/org/{organization_id}/tournament?tournament_id={tournament.id}",
                    )
                )

            # Add async qualifiers
            for tournament in active_async_tournaments:
                sidebar_items.append(
                    base.create_nav_link(
                        f"🏁 {tournament.name}",
                        "schedule",
                        f"/org/{organization_id}/async/{tournament.id}",
                    )
                )

        await base.render(content, sidebar_items, use_dynamic_content=True)

    @ui.page("/org/{organization_id}/tournament")
    async def tournament_org_page(
        organization_id: int, tournament_id: int | None = None
    ):
        """Organization features page for specific organization."""
        base = BasePage.authenticated_page(title="Organization")
        org_service = OrganizationService()
        tournament_service = TournamentService()
        usage_service = TournamentUsageService()

        # Pre-check that user is a member of the organization
        from middleware.auth import DiscordAuthService

        user = await DiscordAuthService.get_current_user()

        # Check if user is a member of this organization
        is_member = await org_service.is_member(user, organization_id)

        # Track tournament usage if tournament_id is provided
        if is_member and tournament_id:
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
            # Re-check membership inside content
            if not is_member:
                ui.notify(
                    "You must be a member of this organization to view organization features.",
                    color="negative",
                )
                ui.navigate.to("/?view=organizations")
                return

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

            # Register content loaders for different sections
            async def load_event_schedule():
                """Load event schedule."""
                view = EventScheduleView(org, page.user)
                if tournament_id:
                    view.selected_tournaments = [tournament_id]
                await page.load_view_into_container(view)

            async def load_my_matches():
                """Load my matches."""
                view = MyMatchesView(org, page.user)
                if tournament_id:
                    view.selected_tournaments = [tournament_id]
                await page.load_view_into_container(view)

            async def load_my_settings():
                """Load my settings."""
                view = MySettingsView(page.user, org, tournament_service)
                await page.load_view_into_container(view)

            # Register loaders
            page.register_content_loader("event_schedule", load_event_schedule)
            page.register_content_loader("my_matches", load_my_matches)
            page.register_content_loader("my_settings", load_my_settings)

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await load_event_schedule()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link(
                "Back to Organization", "arrow_back", f"/org/{organization_id}"
            ),
            base.create_separator(),
        ]
        sidebar_items.extend(
            base.create_sidebar_items(
                [
                    ("Event Schedule", "event", "event_schedule"),
                    ("My Matches", "sports_esports", "my_matches"),
                    ("My Settings", "settings", "my_settings"),
                ]
            )
        )

        await base.render(content, sidebar_items, use_dynamic_content=True)
