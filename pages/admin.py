"""
Admin page for SahaBot2.

This module provides administrative functionality.
"""

from nicegui import ui
from components.base_page import BasePage
from views.admin_users import AdminUsersView
from views import overview, settings


def register():
    """Register admin page routes."""
    
    @ui.page('/admin')
    async def admin_overview():
        """Admin dashboard overview page."""
        base = BasePage.admin_page(title="SahaBot2 - Admin")
        
        async def content(page: BasePage):
            """Render the admin overview content."""
            # Header
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('Admin Dashboard').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label(f'Welcome, {page.user.discord_username}').classes('text-primary')
                    ui.label(f'Permission Level: {page.user.permission.name}').classes('text-secondary')
            
            # Render overview
            await overview.OverviewView.render(page.user)
        
        sidebar_items = [
            {'label': 'Home', 'action': lambda: ui.navigate.to('/'), 'icon': 'home'},
            {'label': 'Overview', 'action': lambda: ui.navigate.to('/admin'), 'icon': 'dashboard'},
            {'label': 'Users', 'action': lambda: ui.navigate.to('/admin/users'), 'icon': 'people'},
            {'label': 'Settings', 'action': lambda: ui.navigate.to('/admin/settings'), 'icon': 'settings'},
        ]
        
        await base.render(content, sidebar_items)
    
    @ui.page('/admin/users')
    async def admin_users():
        """Admin users management page."""
        base = BasePage.admin_page(title="SahaBot2 - User Management")
        
        async def content(page: BasePage):
            """Render the users management content."""
            users_view = AdminUsersView(page.user)
            await users_view.render()
        
        sidebar_items = [
            {'label': 'Home', 'action': lambda: ui.navigate.to('/'), 'icon': 'home'},
            {'label': 'Overview', 'action': lambda: ui.navigate.to('/admin'), 'icon': 'dashboard'},
            {'label': 'Users', 'action': lambda: ui.navigate.to('/admin/users'), 'icon': 'people'},
            {'label': 'Settings', 'action': lambda: ui.navigate.to('/admin/settings'), 'icon': 'settings'},
        ]
        
        await base.render(content, sidebar_items)
    
    @ui.page('/admin/settings')
    async def admin_settings():
        """Admin settings page."""
        base = BasePage.admin_page(title="SahaBot2 - Settings")
        
        async def content(page: BasePage):
            """Render the settings content."""
            await settings.SettingsView.render(page.user)
        
        sidebar_items = [
            {'label': 'Home', 'action': lambda: ui.navigate.to('/'), 'icon': 'home'},
            {'label': 'Overview', 'action': lambda: ui.navigate.to('/admin'), 'icon': 'dashboard'},
            {'label': 'Users', 'action': lambda: ui.navigate.to('/admin/users'), 'icon': 'people'},
            {'label': 'Settings', 'action': lambda: ui.navigate.to('/admin/settings'), 'icon': 'settings'},
        ]
        
        await base.render(content, sidebar_items)
