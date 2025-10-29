"""
Example page demonstrating BasePage usage.

This module shows how to use the BasePage component for different page types.
"""

from nicegui import ui
from components import BasePage


def register():
    """Register example page routes."""

    @ui.page('/example')
    async def example_page():
        """
        Simple example page with no authentication required.

        Demonstrates basic usage of BasePage with sidebar.
        """
        # Create a simple page (no auth required)
        base = BasePage.simple_page(title="Example Page")

        # Define sidebar items
        sidebar_items = [
            {
                'label': 'Home',
                'icon': 'home',
                'action': lambda: ui.navigate.to('/')
            },
            {
                'label': 'Example Page',
                'icon': 'science',
                'action': lambda: ui.navigate.to('/example')
            },
            {
                'label': 'Protected Page',
                'icon': 'lock',
                'action': lambda: ui.navigate.to('/example/protected')
            },
            {
                'label': 'Admin Page',
                'icon': 'admin_panel_settings',
                'action': lambda: ui.navigate.to('/example/admin')
            },
        ]

        async def content(page: BasePage):
            """Render page content."""
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Welcome to the Example Page')

                with ui.element('div').classes('card-body'):
                    ui.label('Click the hamburger menu (☰) in the header to open the sidebar!')
                    ui.label('')
                    if page.user:
                        ui.label(f'Hello, {page.user.discord_username}!')
                        ui.label(f'Permission level: {page.user.permission.name}')
                    else:
                        ui.label('You are not logged in.')
                        ui.label('Click the user menu button in the header to log in.')

        await base.render(content, sidebar_items=sidebar_items)

    @ui.page('/example/protected')
    async def protected_page():
        """
        Protected example page requiring authentication.

        Only logged-in users can access this page.
        """
        # Create authenticated page
        base = BasePage.authenticated_page(title="Protected Page")

        # Define sidebar items
        sidebar_items = [
            {
                'label': 'Home',
                'icon': 'home',
                'action': lambda: ui.navigate.to('/')
            },
            {
                'label': 'Example Page',
                'icon': 'science',
                'action': lambda: ui.navigate.to('/example')
            },
            {
                'label': 'Protected Page',
                'icon': 'lock',
                'action': lambda: ui.navigate.to('/example/protected')
            },
            {
                'label': 'Admin Page',
                'icon': 'admin_panel_settings',
                'action': lambda: ui.navigate.to('/example/admin')
            },
        ]

        async def content(page: BasePage):
            """Render page content."""
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Protected Content')

                with ui.element('div').classes('card-body'):
                    ui.label(f'Welcome, {page.user.discord_username}!')
                    ui.label('This page requires authentication.')
                    ui.label(f'Your permission level: {page.user.permission.name}')

        await base.render(content, sidebar_items=sidebar_items)

    @ui.page('/example/admin')
    async def admin_example_page():
        """
        Admin example page requiring admin permission.

        Only admin users can access this page.
        """
        # Create admin page
        base = BasePage.admin_page(title="Admin Example")

        # Define sidebar items
        sidebar_items = [
            {
                'label': 'Home',
                'icon': 'home',
                'action': lambda: ui.navigate.to('/')
            },
            {
                'label': 'Example Page',
                'icon': 'science',
                'action': lambda: ui.navigate.to('/example')
            },
            {
                'label': 'Protected Page',
                'icon': 'lock',
                'action': lambda: ui.navigate.to('/example/protected')
            },
            {
                'label': 'Admin Page',
                'icon': 'admin_panel_settings',
                'action': lambda: ui.navigate.to('/example/admin')
            },
        ]

        async def content(page: BasePage):
            """Render page content."""
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Admin Only Content')

                with ui.element('div').classes('card-body'):
                    ui.label(f'Welcome, Admin {page.user.discord_username}!')
                    ui.label('This page is only accessible to administrators.')
                    ui.label(f'Your permission level: {page.user.permission.name}')

        await base.render(content, sidebar_items=sidebar_items)
