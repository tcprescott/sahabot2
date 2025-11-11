"""
Home page for SahaBot2.

This module provides the main landing page routes.

Routes:
- /: Main overview page (authenticated users) or welcome page (guests)
- /presets: Randomizer presets browser
- /organizations: Organization selector and management
"""

from nicegui import ui
from components import BasePage
from views.home import OverviewView, WelcomeView, PresetsView
from views.tournaments import TournamentOrgSelectView
from middleware.auth import DiscordAuthService


def _create_sidebar(base: BasePage, active: str) -> list:
    """
    Create sidebar for authenticated users.
    
    Args:
        base: BasePage instance
        active: Active page identifier
        
    Returns:
        List of sidebar items
    """
    user = base.user
    items = [
        base.create_nav_link("Overview", "dashboard", "/", active=(active == "overview")),
        base.create_nav_link("Presets", "code", "/presets", active=(active == "presets")),
        base.create_nav_link("Organizations", "group", "/organizations", active=(active == "organizations")),
        base.create_separator(),
        base.create_nav_link("My Profile", "person", "/profile"),
    ]
    
    # Add admin panel link for admin users
    if user and user.has_permission(user.permission.ADMIN):
        items.append(base.create_separator())
        items.append(base.create_nav_link("Admin Panel", "admin_panel_settings", "/admin"))
    
    return items


def register():
    """Register home page routes."""

    @ui.page("/")
    async def home_page():
        """Main home page - overview for authenticated users, welcome for guests."""
        # Check authentication to determine page mode
        user = await DiscordAuthService.get_current_user()

        if user:
            # Authenticated user - show overview
            base = BasePage.authenticated_page(title="SahaBot2 - Home")

            async def content(page: BasePage):
                """Render overview content."""
                await OverviewView.render(page.user)

            sidebar_items = _create_sidebar(base, "overview")
            await base.render(content, sidebar_items)
        else:
            # Guest - show welcome page
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

    @ui.page("/presets")
    async def presets_page():
        """Presets browser page."""
        base = BasePage.authenticated_page(title="SahaBot2 - Presets")

        async def content(page: BasePage):
            """Render presets browser."""
            view = PresetsView(page.user)
            await view.render()

        sidebar_items = _create_sidebar(base, "presets")
        await base.render(content, sidebar_items)

    @ui.page("/organizations")
    async def organizations_page():
        """Organizations selector page."""
        base = BasePage.authenticated_page(title="SahaBot2 - Organizations")

        async def content(page: BasePage):
            """Render organizations selector."""
            view = TournamentOrgSelectView(page.user)
            await view.render()

        sidebar_items = _create_sidebar(base, "organizations")
        await base.render(content, sidebar_items)
