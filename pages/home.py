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
        # Define 10 example tabs with placeholder content
        def make_tab_content(label: str):
            async def _content():
                with ui.element('div').classes('card bg-dynamic-surface'):
                    with ui.element('div').classes('card-header'):
                        ui.label(f'{label}').classes('text-dynamic-primary')
                    with ui.element('div').classes('card-body'):
                        ui.label(f'This is placeholder content for the {label} tab.')\
                            .classes('text-dynamic-secondary')
                # Also showcase a small paragraph for spacing
                ui.label('Use this space to add real content later.')\
                    .classes('text-dynamic-secondary mt-1')
            return _content

        tabs = [
            {"label": "Overview", "icon": "home", "content": make_tab_content("Overview")},
            {"label": "Schedule", "icon": "event", "content": make_tab_content("Schedule")},
            {"label": "Users", "icon": "people", "content": make_tab_content("Users")},
            {"label": "Reports", "icon": "analytics", "content": make_tab_content("Reports")},
            {"label": "Settings", "icon": "settings", "content": make_tab_content("Settings")},
            {"label": "Favorites", "icon": "star", "content": make_tab_content("Favorites")},
            {"label": "Tools", "icon": "build", "content": make_tab_content("Tools")},
            {"label": "Help", "icon": "help", "content": make_tab_content("Help")},
            {"label": "About", "icon": "info", "content": make_tab_content("About")},
            {"label": "Archive", "icon": "inventory", "content": make_tab_content("Archive")},
        ]

        base = BasePage.simple_page(title="SahaBot2", active_nav="home", tabs=tabs, default_tab="Overview")
        # Enable the responsive sidebar for this example
        base.use_sidebar = True

        # Content function is not used when tabs are provided, but define a no-op to keep API consistent
        async def content(_: BasePage):
            pass

        await base.render(content)()
