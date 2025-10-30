"""
User administration view for managing users.

Provides a comprehensive interface for viewing, editing, and managing user accounts.
"""

from nicegui import ui
from models import User, Permission
from application.services.user_service import UserService
from application.services.authorization_service import AuthorizationService
from application.services.audit_service import AuditService
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class UserEditDialog:
    """Dialog for editing user information and permissions."""
    
    def __init__(
        self,
        target_user: User,
        current_user: User,
        on_save: Optional[Callable] = None
    ):
        """
        Initialize user edit dialog.
        
        Args:
            target_user: User to edit
            current_user: Currently logged in user
            on_save: Callback to execute after successful save
        """
        self.target_user = target_user
        self.current_user = current_user
        self.on_save = on_save
        self.user_service = UserService()
        self.auth_service = AuthorizationService()
        self.audit_service = AuditService()
        
        # State
        self.is_active = target_user.is_active
        self.permission = target_user.permission
    
    async def show(self):
        """Display the edit dialog."""
        with ui.dialog() as dialog, ui.card().classes('min-w-96'):
            # Dialog header
            with ui.row().classes('full-width items-center mb-4'):
                ui.icon('edit').classes('text-2xl')
                ui.label(f'Edit User: {self.target_user.discord_username}').classes('text-xl font-bold')
            
            ui.separator()
            
            # User info (read-only)
            with ui.column().classes('full-width gap-2 my-4'):
                ui.label('User Information').classes('font-bold text-lg')
                
                with ui.row().classes('full-width'):
                    ui.label('Discord ID:').classes('font-semibold')
                    ui.label(str(self.target_user.discord_id))
                
                with ui.row().classes('full-width'):
                    ui.label('Username:').classes('font-semibold')
                    ui.label(self.target_user.discord_username)
                
                if self.target_user.discord_email:
                    with ui.row().classes('full-width'):
                        ui.label('Email:').classes('font-semibold')
                        ui.label(self.target_user.discord_email)
            
            ui.separator()
            
            # Editable fields
            with ui.column().classes('full-width gap-4 my-4'):
                # Account status
                ui.label('Account Status').classes('font-bold text-lg')
                status_switch = ui.switch('Active Account', value=self.is_active)
                status_switch.on('update:model-value', lambda e: setattr(self, 'is_active', e.args))
                
                # Permission level (only if user can change permissions)
                if self.auth_service.can_change_permissions(self.current_user, self.target_user, Permission.USER):
                    ui.label('Permission Level').classes('font-bold text-lg mt-4')
                    
                    # Get available permissions (can't set equal or higher than current user)
                    available_permissions = [
                        p for p in Permission
                        if p < self.current_user.permission
                    ]
                    
                    permission_select = ui.select(
                        label='Permission',
                        options={p: p.name for p in available_permissions},
                        value=self.permission
                    )
                    permission_select.on('update:model-value', lambda e: setattr(self, 'permission', e.args))
                else:
                    with ui.row().classes('full-width'):
                        ui.label('Permission:').classes('font-semibold')
                        badge_class = 'badge-admin' if self.target_user.is_admin() else 'badge-moderator' if self.target_user.is_moderator() else 'badge-user'
                        with ui.element('span').classes(f'badge {badge_class}'):
                            ui.label(self.target_user.permission.name)
            
            ui.separator()
            
            # Action buttons
            with ui.row().classes('full-width justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).classes('btn')
                ui.button('Save Changes', on_click=lambda: self._save_and_close(dialog)).classes('btn btn-primary')
        
        dialog.open()
    
    async def _save_and_close(self, dialog):
        """
        Save changes and close dialog.
        
        Args:
            dialog: Dialog to close
        """
        try:
            # Check if changes were made
            changed = False
            changes = []
            
            # Update active status
            if self.is_active != self.target_user.is_active:
                if self.is_active:
                    await self.user_service.activate_user(self.target_user.id)
                    changes.append('activated account')
                else:
                    await self.user_service.deactivate_user(self.target_user.id)
                    changes.append('deactivated account')
                changed = True
            
            # Update permission
            if self.permission != self.target_user.permission:
                if self.auth_service.can_change_permissions(self.current_user, self.target_user, self.permission):
                    await self.user_service.update_user_permission(self.target_user.id, self.permission)
                    changes.append(f'changed permission to {self.permission.name}')
                    changed = True
                else:
                    ui.notify('You do not have permission to change this user\'s permissions', type='negative')
                    return
            
            if changed:
                # Log the audit entry
                await self.audit_service.log_user_update(
                    user=self.current_user,
                    target_user_id=self.target_user.id,
                    changes=', '.join(changes)
                )
                
                ui.notify(f'User {self.target_user.discord_username} updated successfully', type='positive')
                
                # Call the callback
                if self.on_save:
                    await self.on_save()
            else:
                ui.notify('No changes made', type='info')
            
            dialog.close()
            
        except Exception as e:
            logger.error("Error updating user: %s", e, exc_info=True)
            ui.notify(f'Error updating user: {str(e)}', type='negative')


class AdminUsersView:
    """User administration view with full CRUD capabilities."""
    
    def __init__(self, current_user: User):
        """
        Initialize the admin users view.
        
        Args:
            current_user: Currently authenticated admin user
        """
        self.current_user = current_user
        self.user_service = UserService()
        self.auth_service = AuthorizationService()
        
        # State
        self.users: list[User] = []
        self.search_query = ""
        self.include_inactive = True
        self.table_container = None
    
    async def render(self):
        """Render the user administration interface."""
        with ui.column().classes('full-width gap-md'):
            # Header section
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-header'):
                    ui.label('User Management').classes('text-xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('View and manage user accounts, permissions, and access levels.').classes('text-secondary')
            
            # Search and filters
            with ui.element('div').classes('card'):
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('full-width gap-4 items-center'):
                        # Search input
                        search_input = ui.input(
                            label='Search users',
                            placeholder='Search by username...'
                        ).classes('flex-grow')
                        search_input.on('update:model-value', lambda e: self._on_search_change(e.args))
                        
                        # Include inactive checkbox
                        inactive_switch = ui.switch('Include Inactive', value=self.include_inactive)
                        inactive_switch.on('update:model-value', lambda e: self._on_filter_change(e.args))
                        
                        # Refresh button
                        ui.button(
                            icon='refresh',
                            on_click=self._refresh_users
                        ).classes('btn').props('flat')
            
            # User table
            self.table_container = ui.column().classes('full-width')
            await self._refresh_users()
    
    async def _render_statistics(self):
        """Render user statistics cards."""
        # Load all users for statistics
        all_users = await self.user_service.get_all_users(include_inactive=True)
        
        stats = {
            'total': len(all_users),
            'active': len([u for u in all_users if u.is_active]),
            'admins': len([u for u in all_users if u.is_admin()]),
            'moderators': len([u for u in all_users if u.is_moderator() and not u.is_admin()]),
            'users': len([u for u in all_users if not u.is_moderator()])
        }
        
        with ui.element('div').classes('card'):
            with ui.element('div').classes('card-header'):
                ui.label('Statistics').classes('font-bold')
            with ui.element('div').classes('card-body'):
                with ui.row().classes('full-width gap-8'):
                    # Total users
                    with ui.column().classes('items-center'):
                        ui.label(str(stats['total'])).classes('text-3xl font-bold text-primary')
                        ui.label('Total Users').classes('text-sm text-secondary')
                    
                    # Active users
                    with ui.column().classes('items-center'):
                        ui.label(str(stats['active'])).classes('text-3xl font-bold text-success')
                        ui.label('Active').classes('text-sm text-secondary')
                    
                    # Admins
                    with ui.column().classes('items-center'):
                        ui.label(str(stats['admins'])).classes('text-3xl font-bold text-danger')
                        ui.label('Admins').classes('text-sm text-secondary')
                    
                    # Moderators
                    with ui.column().classes('items-center'):
                        ui.label(str(stats['moderators'])).classes('text-3xl font-bold text-warning')
                        ui.label('Moderators').classes('text-sm text-secondary')
                    
                    # Regular users
                    with ui.column().classes('items-center'):
                        ui.label(str(stats['users'])).classes('text-3xl font-bold text-info')
                        ui.label('Regular Users').classes('text-sm text-secondary')
    
    async def _refresh_users(self):
        """Refresh the user list."""
        try:
            # Load users based on current filters
            if self.search_query:
                self.users = await self.user_service.search_users(self.search_query)
                if not self.include_inactive:
                    self.users = [u for u in self.users if u.is_active]
            else:
                self.users = await self.user_service.get_all_users(include_inactive=self.include_inactive)
            
            # Re-render table
            await self._render_user_table()
            
        except Exception as e:
            logger.error("Error loading users: %s", e, exc_info=True)
            ui.notify(f'Error loading users: {str(e)}', type='negative')
    
    async def _render_user_table(self):
        """Render the user table."""
        if not self.table_container:
            return
        
        # Clear existing content
        self.table_container.clear()
        
        with self.table_container:
            if not self.users:
                with ui.element('div').classes('card'):
                    with ui.element('div').classes('card-body text-center'):
                        ui.label('No users found').classes('text-secondary text-lg')
                        ui.label('Try adjusting your search or filters').classes('text-sm text-secondary')
                return
            
            # Create table
            with ui.element('div').classes('card'):
                with ui.element('table').classes('data-table'):
                    # Table header
                    with ui.element('thead'):
                        with ui.element('tr'):
                            with ui.element('th'):
                                ui.label('User')
                            with ui.element('th'):
                                ui.label('Discord ID')
                            with ui.element('th'):
                                ui.label('Email')
                            with ui.element('th'):
                                ui.label('Permission')
                            with ui.element('th'):
                                ui.label('Status')
                            with ui.element('th'):
                                ui.label('Actions')
                    
                    # Table body
                    with ui.element('tbody'):
                        for user in self.users:
                            await self._render_user_row(user)
    
    async def _render_user_row(self, user: User):
        """
        Render a single user row.
        
        Args:
            user: User to render
        """
        with ui.element('tr'):
            # Username with avatar
            with ui.element('td').props('data-label="User"'):
                with ui.row().classes('items-center gap-2'):
                    # Avatar if available
                    if user.discord_avatar:
                        avatar_url = f"https://cdn.discordapp.com/avatars/{user.discord_id}/{user.discord_avatar}.png"
                        ui.image(avatar_url).classes('w-8 h-8 rounded-full')
                    else:
                        ui.icon('account_circle').classes('text-2xl')
                    
                    ui.label(user.discord_username).classes('font-semibold')
            
            # Discord ID
            with ui.element('td').props('data-label="Discord ID"'):
                ui.label(str(user.discord_id)).classes('text-sm font-mono')
            
            # Email
            with ui.element('td').props('data-label="Email"'):
                if user.discord_email:
                    ui.label(user.discord_email).classes('text-sm')
                else:
                    ui.label('—').classes('text-secondary')
            
            # Permission badge
            with ui.element('td').props('data-label="Permission"'):
                badge_class = 'badge-admin' if user.is_admin() else 'badge-moderator' if user.is_moderator() else 'badge-user'
                with ui.element('span').classes(f'badge {badge_class}'):
                    ui.label(user.permission.name)
            
            # Status badge
            with ui.element('td').props('data-label="Status"'):
                status_class = 'badge-success' if user.is_active else 'badge-danger'
                with ui.element('span').classes(f'badge {status_class}'):
                    ui.label('Active' if user.is_active else 'Inactive')
            
            # Actions
            with ui.element('td').props('data-label="Actions"'):
                with ui.row().classes('gap-1'):
                    # Edit button (only if user can edit this user)
                    if self.auth_service.can_edit_user(self.current_user, user):
                        ui.button(
                            icon='edit',
                            on_click=lambda u=user: self._edit_user(u)
                        ).classes('btn btn-sm').props('flat')
                    else:
                        # Disabled edit button
                        ui.button(
                            icon='edit'
                        ).classes('btn btn-sm').props('flat disable')
    
    async def _edit_user(self, user: User):
        """
        Open edit dialog for user.
        
        Args:
            user: User to edit
        """
        dialog = UserEditDialog(
            target_user=user,
            current_user=self.current_user,
            on_save=self._refresh_users
        )
        await dialog.show()
    
    def _on_search_change(self, value: str):
        """
        Handle search input change.
        
        Args:
            value: New search value
        """
        self.search_query = value
        # Debounce would be nice here, but for now just trigger immediately
        ui.timer(0.5, self._refresh_users, once=True)
    
    async def _on_filter_change(self, include_inactive: bool):
        """
        Handle filter change.
        
        Args:
            include_inactive: Whether to include inactive users
        """
        self.include_inactive = include_inactive
        await self._refresh_users()
