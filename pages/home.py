"""
Home page for SahaBot2.

This module provides the main landing page.
"""

from nicegui import ui
from components import BasePage
from views.home import OverviewView, WelcomeView, PresetsView
from middleware.auth import DiscordAuthService


def register():
    """Register home page routes."""

    @ui.page('/')
    async def home_page():
        """Main home page."""
        base = BasePage.simple_page(title="SahaBot2 - Home")

        # Check authentication to determine sidebar items
        user = await DiscordAuthService.get_current_user()

        async def content(page: BasePage):
            """Render home page content."""
            if page.user:
                # Authenticated user - show overview
                await OverviewView.render(page.user)
            else:
                # Guest - show welcome
                await WelcomeView.render()

        # Create sidebar items based on authentication status
        if user:
            # Authenticated user navigation
            sidebar_items = [
                base.create_nav_link('Overview', 'dashboard', '/'),
                base.create_nav_link('Presets', 'code', '/presets'),
                base.create_nav_link('Organizations', 'group', '/org'),
                base.create_separator(),
                base.create_nav_link('My Profile', 'person', '/profile'),
            ]
        else:
            # Guest navigation
            sidebar_items = [
                base.create_nav_link('Welcome', 'home', '/'),
                base.create_nav_link('Login', 'login', '/auth/login'),
            ]

        await base.render(content, sidebar_items)

    @ui.page('/presets')
    async def presets_page():
        """Presets browsing page."""
        base = BasePage.authenticated_page(title="Randomizer Presets")

        async def content(page: BasePage):
            """Render presets content."""
            view = PresetsView(page.user)
            await view.render()

        # Create sidebar items
        sidebar_items = [
            base.create_nav_link('Overview', 'dashboard', '/'),
            base.create_nav_link('Presets', 'code', '/presets'),
            base.create_nav_link('Organizations', 'group', '/org'),
            base.create_separator(),
            base.create_nav_link('My Profile', 'person', '/profile'),
        ]

        await base.render(content, sidebar_items)