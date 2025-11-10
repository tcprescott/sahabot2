"""
Async Qualifier-specific admin page.

Accessible by tournament managers and organization admins.
Provides detailed async qualifier management with dedicated views for different aspects.
"""

from __future__ import annotations
from nicegui import ui
from components.base_page import BasePage
from application.services.organizations.organization_service import OrganizationService
from application.services.tournaments.async_qualifier_service import (
    AsyncQualifierService,
)
from views.tournaments import AsyncDashboardView


def register():
    """Register async qualifier admin page routes."""

    @ui.page("/org/{organization_id}/async/{qualifier_id}/admin")
    async def async_qualifier_admin_page(organization_id: int, qualifier_id: int):
        """Async qualifier administration page."""
        base = BasePage.authenticated_page(title="Async Qualifier Admin")
        org_service = OrganizationService()
        async_service = AsyncQualifierService()

        # Pre-check authorization
        from middleware.auth import DiscordAuthService

        user = await DiscordAuthService.get_current_user()
        can_manage = await org_service.user_can_manage_tournaments(
            user, organization_id
        )

        async def content(page: BasePage):
            """Render async qualifier admin content."""
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

            # Get async qualifier
            qualifier = await async_service.get_tournament(
                page.user, organization_id, qualifier_id
            )
            if not qualifier:
                ui.label("Async qualifier not found").classes("text-negative")
                return

            # Qualifier header
            with ui.element("div").classes("card mb-4"):
                with ui.element("div").classes("card-header"):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(qualifier.name).classes("text-2xl font-bold")
                        ui.button(
                            "View Dashboard",
                            icon="visibility",
                            on_click=lambda: ui.navigate.to(
                                f"/org/{organization_id}/async/{qualifier_id}"
                            ),
                        ).classes("btn")

            # Register content loaders for different sections
            async def load_overview():
                """Load async qualifier overview/dashboard."""
                view = AsyncDashboardView(page.user, qualifier)
                await page.load_view_into_container(view)

            async def load_settings():
                """Load async qualifier settings."""
                container = page.get_dynamic_content_container()
                if container:
                    container.clear()
                    with container:
                        # For now, just show a placeholder
                        # Could expand this to dedicated settings view later
                        ui.label("Async Qualifier Settings").classes(
                            "text-xl font-bold"
                        )
                        ui.label(
                            "Coming soon - use Organization Admin > Async Qualifiers to edit"
                        ).classes("text-secondary")

            # Register loaders
            page.register_content_loader("overview", load_overview)
            page.register_content_loader("settings", load_settings)

            # Load initial content only if no view parameter was specified
            if not page.initial_view:
                await load_overview()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link(
                "Back to Organization",
                "arrow_back",
                f"/orgs/{organization_id}/admin?view=async_tournaments",
            ),
            base.create_separator(),
        ]
        sidebar_items.extend(base.create_sidebar_items([
            ("Overview", "dashboard", "overview"),
            ("Settings", "tune", "settings"),
        ]))

        await base.render(content, sidebar_items, use_dynamic_content=True)
