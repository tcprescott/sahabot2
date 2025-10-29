"""
Admin page for SahaBot2.

This module provides administrative functionality.
"""

from nicegui import ui
from components.base_page import BasePage
from application.services.user_service import UserService
from application.services.authorization_service import AuthorizationService


def register():
    """Register admin page routes."""
    
    @ui.page('/admin')
    async def admin_page():
        """
        Admin dashboard page.
        
        Requires admin permissions.
        """
        base = BasePage.admin_page(title="SahaBot2 - Admin", active_nav="admin")
        
        async def content(page: BasePage):
            """Render the admin page content."""
            # Initialize services
            user_service = UserService()
            auth_z_service = AuthorizationService()
            
            # Header
            with ui.element('div').classes('card'):
                ui.element('div').classes('card-header').text('Admin Dashboard')
                with ui.element('div').classes('card-body'):
                    ui.label(f'Welcome, {page.user.discord_username}').classes('text-primary')
                    ui.label(f'Permission Level: {page.user.permission.name}').classes('text-secondary')
            
            # User management section
            with ui.element('div').classes('card'):
                ui.element('div').classes('card-header').text('User Management')
                
                # User list
                users = await user_service.get_all_users(include_inactive=True)
                
                if users:
                    with ui.element('table').classes('data-table'):
                        # Table header
                        with ui.element('thead'):
                            with ui.element('tr'):
                                with ui.element('th'):
                                    ui.label('Username')
                                with ui.element('th'):
                                    ui.label('Discord ID')
                                with ui.element('th'):
                                    ui.label('Permission')
                                with ui.element('th'):
                                    ui.label('Status')
                                with ui.element('th'):
                                    ui.label('Actions')
                        
                        # Table body
                        with ui.element('tbody'):
                            for u in users:
                                with ui.element('tr'):
                                    with ui.element('td').props('data-label="Username"'):
                                        ui.label(u.discord_username)
                                    with ui.element('td').props('data-label="Discord ID"'):
                                        ui.label(str(u.discord_id))
                                    with ui.element('td').props('data-label="Permission"'):
                                        badge_class = 'badge-admin' if u.is_admin() else 'badge-moderator' if u.is_moderator() else 'badge-user'
                                        ui.element('span').classes(f'badge {badge_class}').text(u.permission.name)
                                    with ui.element('td').props('data-label="Status"'):
                                        status_class = 'badge-success' if u.is_active else 'badge-danger'
                                        ui.element('span').classes(f'badge {status_class}').text('Active' if u.is_active else 'Inactive')
                                    with ui.element('td').props('data-label="Actions"'):
                                        if auth_z_service.can_edit_user(page.user, u):
                                            ui.button('Edit', on_click=lambda u=u: edit_user(u)).classes('btn btn-sm')
                else:
                    ui.label('No users found.').classes('text-secondary')
            
            async def edit_user(target_user):
                """
                Edit user dialog.
                
                Args:
                    target_user: User to edit
                """
                ui.notify(f'Edit user: {target_user.discord_username}')
                # TODO: Implement edit user dialog
        
        await base.render(content)()
