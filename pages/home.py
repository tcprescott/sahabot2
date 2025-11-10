"""
Home page for SahaBot2.

This module provides the main landing page with dynamic content loading.

For authenticated users, the page supports multiple views:
- Overview: Dashboard with user information
- Presets: Randomizer presets browser
- Organizations: Organization selector and management
"""

from typing import Optional
from nicegui import ui
from components import BasePage
from views.home import OverviewView, WelcomeView, PresetsView
from views.tournaments import TournamentOrgSelectView
from middleware.auth import DiscordAuthService


def register():
    """Register home page routes."""

    @ui.page("/")
    @ui.page("/{view}")
    async def home_page(view: Optional[str] = None):
        """Main home page."""
        # Check authentication to determine page mode
        user = await DiscordAuthService.get_current_user()

        if user:
            # Authenticated user - dynamic content page
            base = BasePage.authenticated_page(title="SahaBot2 - Home", view=view)

            async def content(page: BasePage):
                """Render home page content with dynamic views."""

                # Define content loader functions
                async def load_overview():
                    """Load the overview content."""
                    container = page.get_dynamic_content_container() or ui.element(
                        "div"
                    ).classes("page-container")
                    container.clear()
                    with container:
                        await OverviewView.render(page.user)

                async def load_presets():
                    """Load the presets browser."""
                    container = page.get_dynamic_content_container() or ui.element(
                        "div"
                    ).classes("page-container")
                    container.clear()
                    with container:
                        view = PresetsView(page.user)
                        await view.render()

                async def load_organizations():
                    """Load the organizations selector."""
                    container = page.get_dynamic_content_container() or ui.element(
                        "div"
                    ).classes("page-container")
                    container.clear()
                    with container:
                        view = TournamentOrgSelectView(page.user)
                        await view.render()

                # Register content loaders
                page.register_content_loader("overview", load_overview)
                page.register_content_loader("presets", load_presets)
                page.register_content_loader("organizations", load_organizations)

                # Load initial content only if no view parameter was specified
                if not page.initial_view:
                    await load_overview()

            # Create sidebar items with dynamic content loaders
            sidebar_items = base.create_sidebar_items([
                ("Overview", "dashboard", "overview"),
                ("Presets", "code", "presets"),
                ("Organizations", "group", "organizations"),
            ])
            sidebar_items.append(base.create_separator())
            sidebar_items.append(base.create_nav_link("My Profile", "person", "/profile"))
            # Add admin panel link for admin users
            if user.is_admin():
                sidebar_items.append(base.create_separator())
                sidebar_items.append(
                    base.create_nav_link(
                        "Admin Panel", "admin_panel_settings", "/admin"
                    )
                )

            await base.render(content, sidebar_items, use_dynamic_content=True)
        else:
            # Guest - simple static page
            base = BasePage.simple_page(title="SahaBot2 - Home")

            async def content(_page: BasePage):
                """Render welcome content for guests."""
                await WelcomeView.render()

            # Guest navigation
            sidebar_items = [
                base.create_nav_link("Welcome", "home", "/"),
                base.create_nav_link("Login", "login", "/auth/login"),
            ]

            await base.render(content, sidebar_items)
