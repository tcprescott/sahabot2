"""
Async Qualifiers page.

Shows organization-scoped async qualifier views.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organizations.organization_service import OrganizationService
from application.services.tournaments import TournamentService
from plugins.builtin.async_qualifier.services import (
    AsyncQualifierService,
)
from views.async_qualifiers import (
    AsyncDashboardView,
    AsyncLeaderboardView,
    AsyncPoolsView,
    AsyncPlayerHistoryView,
    AsyncPermalinkView,
    AsyncReviewQueueView,
)


def register():
    """Register async qualifier page routes."""

    @ui.page("/org/{organization_id}/async")
    async def async_qualifier_overview_page(organization_id: int):
        """Async qualifiers overview page for an organization."""
        base = BasePage.authenticated_page(title="Async Qualifiers")
        org_service = OrganizationService()
        tournament_service = TournamentService()
        async_tournament_service = AsyncQualifierService()

        # Pre-check that user is a member of the organization
        from middleware.auth import DiscordAuthService

        user = await DiscordAuthService.get_current_user()

        # Check if user is a member of this organization
        is_member = await org_service.is_member(user, organization_id)

        # Get active tournaments for sidebar (using service layer)
        active_async_tournaments = (
            await async_tournament_service.list_active_org_tournaments(
                user, organization_id
            )
        )
        active_tournaments = await tournament_service.list_active_org_tournaments(
            user, organization_id
        )

        async def content(_page: BasePage):
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

            # Get all async qualifiers for this organization (using service layer)
            all_tournaments = await async_tournament_service.list_org_tournaments(
                user, organization_id
            )
            active = [t for t in all_tournaments if t.is_active]
            inactive = [t for t in all_tournaments if not t.is_active]

            from components.card import Card
            from components.datetime_label import DateTimeLabel

            # Header
            with Card.create(title="Async Qualifiers"):
                with ui.column().classes("gap-md"):
                    ui.label(
                        f"View and participate in async qualifiers for {org.name}"
                    ).classes("text-secondary")

                    if active:
                        ui.separator()
                        ui.label("Active Tournaments").classes("text-lg font-semibold")
                        with ui.column().classes("gap-sm"):
                            for tournament in active:
                                with ui.element("div").classes("card"):
                                    with ui.element("div").classes("card-body"):
                                        with ui.row().classes(
                                            "w-full items-center justify-between"
                                        ):
                                            with ui.column().classes("gap-1"):
                                                ui.link(
                                                    tournament.name,
                                                    f"/org/{organization_id}/async/{tournament.id}",
                                                ).classes("text-xl font-semibold")
                                                if tournament.description:
                                                    ui.label(
                                                        tournament.description
                                                    ).classes("text-secondary text-sm")
                                                with ui.row().classes(
                                                    "gap-md items-center"
                                                ):
                                                    ui.label("Created:").classes(
                                                        "text-sm text-secondary"
                                                    )
                                                    DateTimeLabel.datetime(
                                                        tournament.created_at
                                                    )
                                            with ui.column().classes("items-end gap-1"):
                                                ui.label("Active").classes(
                                                    "badge badge-success"
                                                )
                                                ui.button(
                                                    "View Dashboard",
                                                    icon="arrow_forward",
                                                    on_click=lambda t=tournament: ui.navigate.to(
                                                        f"/org/{organization_id}/async/{t.id}"
                                                    ),
                                                ).classes("btn btn-primary")

                    if inactive:
                        ui.separator()
                        ui.label("Past Tournaments").classes("text-lg font-semibold")
                        with ui.column().classes("gap-sm"):
                            for tournament in inactive:
                                with ui.element("div").classes("card"):
                                    with ui.element("div").classes("card-body"):
                                        with ui.row().classes(
                                            "w-full items-center justify-between"
                                        ):
                                            with ui.column().classes("gap-1"):
                                                ui.link(
                                                    tournament.name,
                                                    f"/org/{organization_id}/async/{tournament.id}",
                                                ).classes("text-xl font-semibold")
                                                if tournament.description:
                                                    ui.label(
                                                        tournament.description
                                                    ).classes("text-secondary text-sm")
                                                with ui.row().classes(
                                                    "gap-md items-center"
                                                ):
                                                    ui.label("Created:").classes(
                                                        "text-sm text-secondary"
                                                    )
                                                    DateTimeLabel.datetime(
                                                        tournament.created_at
                                                    )
                                            with ui.column().classes("items-end gap-1"):
                                                ui.label("Closed").classes(
                                                    "badge badge-danger"
                                                )
                                                ui.button(
                                                    "View Results",
                                                    icon="arrow_forward",
                                                    on_click=lambda t=tournament: ui.navigate.to(
                                                        f"/org/{organization_id}/async/{t.id}"
                                                    ),
                                                ).classes("btn")

                    if not all_tournaments:
                        with ui.element("div").classes("text-center mt-4"):
                            ui.icon("schedule").classes("text-secondary icon-large")
                            ui.label("No async qualifiers yet").classes(
                                "text-secondary"
                            )
                            ui.label("Ask an administrator to create one").classes(
                                "text-secondary text-sm"
                            )

        # Create sidebar items (same as organization overview)
        sidebar_items = [
            base.create_nav_link(
                "Back to Organization", "arrow_back", f"/org/{organization_id}"
            ),
            base.create_separator(),
        ]

        # Add active tournament links if there are any
        if active_tournaments or active_async_tournaments:
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

        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/async/{tournament_id}")
    async def async_qualifier_dashboard(organization_id: int, tournament_id: int):
        """Async qualifier dashboard - player's own races."""
        base = BasePage.authenticated_page(title="Async Qualifier")

        from plugins.builtin.async_qualifier.services import (
            AsyncQualifierService,
        )

        async_service = AsyncQualifierService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(
                page.user, organization_id, tournament_id
            )
            if not tournament:
                ui.label("Tournament not found or you do not have access").classes(
                    "text-danger"
                )
                return

            view = AsyncDashboardView(page.user, tournament)
            await view.render()

        sidebar_items = [
            base.create_nav_link(
                "Back to Organization", "arrow_back", f"/org/{organization_id}"
            ),
        ]

        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/async/{tournament_id}/leaderboard")
    async def async_qualifier_leaderboard(organization_id: int, tournament_id: int):
        """Async qualifier leaderboard."""
        base = BasePage.authenticated_page(title="Async Qualifier Leaderboard")

        from plugins.builtin.async_qualifier.services import (
            AsyncQualifierService,
        )

        async_service = AsyncQualifierService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(
                page.user, organization_id, tournament_id
            )
            if not tournament:
                ui.label("Tournament not found or you do not have access").classes(
                    "text-danger"
                )
                return

            view = AsyncLeaderboardView(page.user, tournament)
            await view.render()

        sidebar_items = [
            base.create_nav_link(
                "Dashboard",
                "dashboard",
                f"/org/{organization_id}/async/{tournament_id}",
            ),
            base.create_nav_link(
                "Leaderboard",
                "leaderboard",
                f"/org/{organization_id}/async/{tournament_id}/leaderboard",
            ),
            base.create_nav_link(
                "Pools", "folder", f"/org/{organization_id}/async/{tournament_id}/pools"
            ),
        ]

        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/async/{tournament_id}/pools")
    async def async_qualifier_pools(organization_id: int, tournament_id: int):
        """Async qualifier pools."""
        base = BasePage.authenticated_page(title="Async Qualifier Pools")

        from plugins.builtin.async_qualifier.services import (
            AsyncQualifierService,
        )

        async_service = AsyncQualifierService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(
                page.user, organization_id, tournament_id
            )
            if not tournament:
                ui.label("Tournament not found or you do not have access").classes(
                    "text-danger"
                )
                return

            view = AsyncPoolsView(page.user, tournament)
            await view.render()

        sidebar_items = [
            base.create_nav_link(
                "Dashboard",
                "dashboard",
                f"/org/{organization_id}/async/{tournament_id}",
            ),
            base.create_nav_link(
                "Leaderboard",
                "leaderboard",
                f"/org/{organization_id}/async/{tournament_id}/leaderboard",
            ),
            base.create_nav_link(
                "Pools", "folder", f"/org/{organization_id}/async/{tournament_id}/pools"
            ),
        ]

        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/async/{tournament_id}/player/{player_id}")
    async def async_qualifier_player(
        organization_id: int, tournament_id: int, player_id: int
    ):
        """Async qualifier player history."""
        base = BasePage.authenticated_page(title="Player History")

        from plugins.builtin.async_qualifier.services import (
            AsyncQualifierService,
        )

        async_service = AsyncQualifierService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(
                page.user, organization_id, tournament_id
            )
            if not tournament:
                ui.label("Tournament not found or you do not have access").classes(
                    "text-danger"
                )
                return

            view = AsyncPlayerHistoryView(page.user, tournament, player_id)
            await view.render()

        sidebar_items = [
            base.create_nav_link(
                "Dashboard",
                "dashboard",
                f"/org/{organization_id}/async/{tournament_id}",
            ),
            base.create_nav_link(
                "Leaderboard",
                "leaderboard",
                f"/org/{organization_id}/async/{tournament_id}/leaderboard",
            ),
        ]

        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/async/{tournament_id}/permalink/{permalink_id}")
    async def async_qualifier_permalink(
        organization_id: int, tournament_id: int, permalink_id: int
    ):
        """Async qualifier permalink view."""
        base = BasePage.authenticated_page(title="Permalink Races")

        from plugins.builtin.async_qualifier.services import (
            AsyncQualifierService,
        )

        async_service = AsyncQualifierService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(
                page.user, organization_id, tournament_id
            )
            if not tournament:
                ui.label("Tournament not found or you do not have access").classes(
                    "text-danger"
                )
                return

            view = AsyncPermalinkView(page.user, tournament, permalink_id)
            await view.render()

        sidebar_items = [
            base.create_nav_link(
                "Dashboard",
                "dashboard",
                f"/org/{organization_id}/async/{tournament_id}",
            ),
            base.create_nav_link(
                "Leaderboard",
                "leaderboard",
                f"/org/{organization_id}/async/{tournament_id}/leaderboard",
            ),
            base.create_nav_link(
                "Pools", "folder", f"/org/{organization_id}/async/{tournament_id}/pools"
            ),
        ]

        await base.render(content, sidebar_items)

    @ui.page("/org/{organization_id}/async/{tournament_id}/review")
    async def async_qualifier_review_queue(organization_id: int, tournament_id: int):
        """Async qualifier review queue - for reviewers only."""
        base = BasePage.authenticated_page(title="Race Review Queue")

        from plugins.builtin.async_qualifier.services import (
            AsyncQualifierService,
        )

        async_service = AsyncQualifierService()

        async def content(page: BasePage):
            # Get tournament
            tournament = await async_service.get_tournament(
                page.user, organization_id, tournament_id
            )
            if not tournament:
                ui.label("Tournament not found or you do not have access").classes(
                    "text-danger"
                )
                return

            # Check if user has review permissions
            can_review = await async_service.can_review_async_races(
                page.user, organization_id
            )
            if not can_review:
                ui.label("You do not have permission to review races").classes(
                    "text-danger"
                )
                return

            view = AsyncReviewQueueView(tournament, page.user, organization_id)
            await view.render()

        sidebar_items = [
            base.create_nav_link(
                "Dashboard",
                "dashboard",
                f"/org/{organization_id}/async/{tournament_id}",
            ),
            base.create_nav_link(
                "Leaderboard",
                "leaderboard",
                f"/org/{organization_id}/async/{tournament_id}/leaderboard",
            ),
            base.create_nav_link(
                "Pools", "folder", f"/org/{organization_id}/async/{tournament_id}/pools"
            ),
            base.create_separator(),
            base.create_nav_link(
                "Review Queue",
                "rate_review",
                f"/org/{organization_id}/async/{tournament_id}/review",
            ),
        ]

        await base.render(content, sidebar_items)
