"""
Home page for SahaBot2.

This module provides the main landing page for the application.
"""

from nicegui import ui
from components import BasePage
from views import OverviewView


def register():
    """Register home page routes."""

    @ui.page('/')
    async def home_page():
        """
        Main home page.

        Displays welcome message and user dashboard if authenticated.
        """
        # Create page
        base = BasePage.simple_page(title="SahaBot2 - Home")

        # Define sidebar navigation items
        sidebar_items = [
            {
                'label': 'Overview',
                'icon': 'home',
                'action': lambda: ui.notify('Overview selected')
            },
            {
                'label': 'Schedule',
                'icon': 'event',
                'action': lambda: ui.notify('Schedule selected')
            },
            {
                'label': 'Users',
                'icon': 'people',
                'action': lambda: ui.notify('Users selected')
            },
            {
                'label': 'Reports',
                'icon': 'analytics',
                'action': lambda: ui.notify('Reports selected')
            },
            {
                'label': 'Settings',
                'icon': 'settings',
                'action': lambda: ui.notify('Settings selected')
            },
            {
                'label': 'Favorites',
                'icon': 'star',
                'action': lambda: ui.notify('Favorites selected')
            },
            {
                'label': 'Tools',
                'icon': 'build',
                'action': lambda: ui.notify('Tools selected')
            },
            {
                'label': 'Help',
                'icon': 'help',
                'action': lambda: ui.notify('Help selected')
            },
            {
                'label': 'About',
                'icon': 'info',
                'action': lambda: ui.notify('About selected')
            },
        ]

        async def content(page: BasePage):
            """Render home page content."""
            if page.user:
                # Logged in user - show overview
                await OverviewView.render(page.user)
            else:
                # Not logged in - show welcome message
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

        await base.render(content, sidebar_items=sidebar_items)