"""
Home page for SahaBot2.

This module provides the main landing page with dynamic content loading.

Uses BasePage's dynamic content switching via sidebar navigation for:
- Overview, Schedule, Users, Reports, Settings, Favorites, Tools, Help, About
"""

from nicegui import ui
from components import BasePage
from views.home import (
    overview, schedule, users, reports, settings,
    favorites, tools, help as help_view, about, welcome
)


def register():
    """Register home page routes."""

    @ui.page('/')
    async def home_page():
        """
        Main home page with dynamic content switching.

        Displays welcome message for guests or dynamic dashboard for authenticated users.
        """
        # Create page
        base = BasePage.simple_page(title="SahaBot2 - Home")

        async def content(page: BasePage):
            """Render home page with dynamic content container."""
            # Dynamic content is managed by BasePage; use page.create_view_loader for loaders
            
            # Use BasePage factory method for content loaders (shared across pages)
            
            # Register content loaders using the factory
            page.register_content_loader('overview', page.create_view_loader(overview.OverviewView))
            page.register_content_loader('schedule', page.create_view_loader(schedule.ScheduleView))
            page.register_content_loader('users', page.create_view_loader(users.UsersView))
            page.register_content_loader('reports', page.create_view_loader(reports.ReportsView))
            page.register_content_loader('settings', page.create_view_loader(settings.SettingsView))
            page.register_content_loader('favorites', page.create_view_loader(favorites.FavoritesView))
            page.register_content_loader('tools', page.create_view_loader(tools.ToolsView))
            page.register_content_loader('help', page.create_view_loader(help_view.HelpView))
            page.register_content_loader('about', page.create_view_loader(about.AboutView))
            
            # Load initial content based on auth status
            if page.user:
                await page.create_view_loader(overview.OverviewView)()
            else:
                await page.create_view_loader(welcome.WelcomeView)()
        
        # Create sidebar items with dynamic content loaders
        # Demonstrate subsections: group related items under collapsible headers
        management_section = base.create_sidebar_section(
            label='Management',
            icon='folder',
            children=[
                base.create_sidebar_item_with_loader('Users', 'people', 'users'),
                base.create_sidebar_item_with_loader('Reports', 'analytics', 'reports'),
                base.create_sidebar_item_with_loader('Settings', 'settings', 'settings'),
            ],
        )

        resources_section = base.create_sidebar_section(
            label='Resources',
            icon='menu_book',
            children=[
                base.create_sidebar_item_with_loader('Favorites', 'star', 'favorites'),
                base.create_sidebar_item_with_loader('Tools', 'build', 'tools'),
                base.create_sidebar_item_with_loader('Help', 'help', 'help'),
                base.create_sidebar_item_with_loader('About', 'info', 'about'),
            ],
        )

        sidebar_items = [
            base.create_sidebar_item_with_loader('Overview', 'home', 'overview'),
            base.create_sidebar_item_with_loader('Schedule', 'event', 'schedule'),
            {'type': 'separator'},
            management_section,
            resources_section,
        ]
        
        await base.render(content, sidebar_items, use_dynamic_content=True)