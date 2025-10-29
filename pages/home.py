"""
Home page for SahaBot2.

This module provides the main landing page for the application.
"""

from nicegui import ui
from components import BasePage
from views import (
    OverviewView,
    ScheduleView,
    UsersView,
    ReportsView,
    SettingsView,
    FavoritesView,
    ToolsView,
    HelpView,
    AboutView,
    ArchiveView,
)


def register():
    """Register home page routes."""
    
    @ui.page('/')
    async def home_page():
        """
        Main home page.
        
        Displays welcome message and user dashboard if authenticated.
        """
        # Create wrapper functions that call view render methods with the user
        # Tab content functions may be called with a 'page' argument by BasePage
        # We'll use authenticated_page which gives us access to user via page.user
        def make_view_content(view_class):
            async def _content(page: BasePage):
                # Use the user from the page object
                if page.user:
                    await view_class.render(page.user)
            return _content

        # Define tabs with dedicated view modules
        tabs = [
            {"label": "Overview", "icon": "home", "content": make_view_content(OverviewView)},
            {"label": "Schedule", "icon": "event", "content": make_view_content(ScheduleView)},
            {"label": "Users", "icon": "people", "content": make_view_content(UsersView)},
            {"label": "Reports", "icon": "analytics", "content": make_view_content(ReportsView)},
            {"label": "Settings", "icon": "settings", "content": make_view_content(SettingsView)},
            {"label": "Favorites", "icon": "star", "content": make_view_content(FavoritesView)},
            {"label": "Tools", "icon": "build", "content": make_view_content(ToolsView)},
            {"label": "Help", "icon": "help", "content": make_view_content(HelpView)},
            {"label": "About", "icon": "info", "content": make_view_content(AboutView)},
            {"label": "Archive", "icon": "inventory", "content": make_view_content(ArchiveView)},
        ]

        base = BasePage.simple_page(title="SahaBot2", active_nav="home", tabs=tabs, default_tab="Overview")
        # Enable the responsive sidebar for this example
        base.use_sidebar = True

        # Content function is not used when tabs are provided, but define a no-op to keep API consistent
        async def content(_: BasePage):
            pass

        await base.render(content)()
