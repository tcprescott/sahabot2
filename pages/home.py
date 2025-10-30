"""
Home page for SahaBot2.

This module provides the main landing page with dynamic content loading.

Uses BasePage's dynamic content switching via sidebar navigation for:
- Overview, Schedule, Users, Reports, Settings, Favorites, Tools, Help, About
"""

from nicegui import ui
from components import BasePage
from views import (
    overview, schedule, users, reports, settings,
    favorites, tools, help as help_view, about
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
            # Get the dynamic content container
            container = page.get_dynamic_content_container()
            
            # Define content loader functions
            async def load_welcome():
                """Load welcome page for non-authenticated users."""
                container.clear()
                with container:
                    with ui.element('div').classes('home-hero'):
                        ui.label('Welcome to SahaBot2').style('font-size: 2rem; font-weight: 700; margin-bottom: 1rem;')
                        ui.label('A modern Discord bot management platform.').style('font-size: 1.2rem; margin-bottom: 1rem;')
                        ui.label('Log in with Discord to get started!').style('font-size: 1rem; opacity: 0.8;')

                    # Features section
                    with ui.element('div').classes('card'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Features')

                        with ui.element('div').classes('card-body'):
                            with ui.row().classes('gap-md'):
                                ui.icon('dashboard', size='lg').classes('text-primary')
                                with ui.column().classes('gap-xs'):
                                    ui.label('Dashboard Overview').style('font-weight: 600;')
                                    ui.label('Monitor your bot activity and statistics').classes('text-dynamic-secondary')

                            with ui.row().classes('gap-md mt-1'):
                                ui.icon('people', size='lg').classes('text-primary')
                                with ui.column().classes('gap-xs'):
                                    ui.label('User Management').style('font-weight: 600;')
                                    ui.label('Manage users and permissions').classes('text-dynamic-secondary')

                            with ui.row().classes('gap-md mt-1'):
                                ui.icon('settings', size='lg').classes('text-primary')
                                with ui.column().classes('gap-xs'):
                                    ui.label('Configuration').style('font-weight: 600;')
                                    ui.label('Customize your bot settings').classes('text-dynamic-secondary')

                    # Getting started section
                    with ui.element('div').classes('card mt-1'):
                        with ui.element('div').classes('card-header'):
                            ui.label('Getting Started')

                        with ui.element('div').classes('card-body'):
                            ui.label('1. Click the user menu button (top right) to log in with Discord').classes('text-dynamic-secondary')
                            ui.label('2. Use the hamburger menu (☰) to navigate between sections').classes('text-dynamic-secondary mt-1')
                            ui.label('3. Explore the features available to you based on your permissions').classes('text-dynamic-secondary mt-1')
            
            async def load_overview():
                """Load overview content."""
                container.clear()
                with container:
                    await overview.OverviewView.render(page.user)
            
            async def load_schedule():
                """Load schedule content."""
                container.clear()
                with container:
                    await schedule.ScheduleView.render(page.user)
            
            async def load_users():
                """Load users content."""
                container.clear()
                with container:
                    await users.UsersView.render(page.user)
            
            async def load_reports():
                """Load reports content."""
                container.clear()
                with container:
                    await reports.ReportsView.render(page.user)
            
            async def load_settings():
                """Load settings content."""
                container.clear()
                with container:
                    await settings.SettingsView.render(page.user)
            
            async def load_favorites():
                """Load favorites content."""
                container.clear()
                with container:
                    await favorites.FavoritesView.render(page.user)
            
            async def load_tools():
                """Load tools content."""
                container.clear()
                with container:
                    await tools.ToolsView.render(page.user)
            
            async def load_help():
                """Load help content."""
                container.clear()
                with container:
                    await help_view.HelpView.render(page.user)
            
            async def load_about():
                """Load about content."""
                container.clear()
                with container:
                    await about.AboutView.render(page.user)
            
            # Register content loaders
            page.register_content_loader('overview', load_overview)
            page.register_content_loader('schedule', load_schedule)
            page.register_content_loader('users', load_users)
            page.register_content_loader('reports', load_reports)
            page.register_content_loader('settings', load_settings)
            page.register_content_loader('favorites', load_favorites)
            page.register_content_loader('tools', load_tools)
            page.register_content_loader('help', load_help)
            page.register_content_loader('about', load_about)
            
            # Load initial content based on auth status
            if page.user:
                await load_overview()
            else:
                await load_welcome()
        
        # Create sidebar items with dynamic content loaders
        sidebar_items = [
            base.create_sidebar_item_with_loader('Overview', 'home', 'overview'),
            base.create_sidebar_item_with_loader('Schedule', 'event', 'schedule'),
            base.create_sidebar_item_with_loader('Users', 'people', 'users'),
            base.create_sidebar_item_with_loader('Reports', 'analytics', 'reports'),
            base.create_sidebar_item_with_loader('Settings', 'settings', 'settings'),
            base.create_sidebar_item_with_loader('Favorites', 'star', 'favorites'),
            base.create_sidebar_item_with_loader('Tools', 'build', 'tools'),
            base.create_sidebar_item_with_loader('Help', 'help', 'help'),
            base.create_sidebar_item_with_loader('About', 'info', 'about'),
        ]
        
        await base.render(content, sidebar_items, use_dynamic_content=True)