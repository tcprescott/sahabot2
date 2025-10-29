"""
Home page for SahaBot2.

This module provides the main landing page for the application.
"""

from nicegui import ui
from components.base_page import BasePage


def register():
    """Register home page routes."""
    
    @ui.page('/')
    async def home_page():
        """
        Main home page.
        
        Displays welcome message and user dashboard if authenticated.
        """
        base = BasePage.simple_page(title="SahaBot2", active_nav="home")
        
        async def content(page: BasePage):
            """Render the home page content."""
            # Welcome card
            with ui.element('div').classes('card'):
                ui.element('div').classes('card-header').text('Welcome to SahaBot2')
                with ui.element('div').classes('card-body'):
                    if page.user:
                        ui.label(f'Hello, {page.user.discord_username}!').classes('text-primary')
                        ui.label(f'Permission Level: {page.user.permission.name}').classes('text-secondary')
                    else:
                        ui.label('Please log in with Discord to continue.').classes('text-secondary')
            
            # User dashboard (if authenticated)
            if page.user:
                with ui.element('div').classes('card'):
                    ui.element('div').classes('card-header').text('Dashboard')
                    with ui.element('div').classes('card-body'):
                        ui.label('Your dashboard content will appear here.').classes('text-secondary')
        
        await base.render(content)()
