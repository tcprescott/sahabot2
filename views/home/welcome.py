"""
Welcome view for non-authenticated users.

Displays landing page information and getting started guide.
"""

from nicegui import ui
from models import User
from typing import Optional


class WelcomeView:
    """Welcome view for the home page."""
    
    @staticmethod
    async def render(user: Optional[User] = None):
        """
        Render the welcome content.
        
        Args:
            user: Current user (unused, for consistency with other views)
        """
        # Reference user to avoid linter warnings about unused parameter
        _ = user
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
