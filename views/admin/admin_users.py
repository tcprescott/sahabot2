"""
User administration view for managing users.

Provides a comprehensive interface for viewing, editing, and managing user accounts.
"""

from nicegui import ui
from components.data_table import ResponsiveTable, TableColumn
from models import User
from models.user import Permission
from application.services.core.user_service import UserService
from components.dialogs import UserEditDialog, UserAddDialog
from components.dialogs.admin.racetime_unlink_dialog import RacetimeUnlinkDialog
from components.datetime_label import DateTimeLabel
import logging

logger = logging.getLogger(__name__)




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
                    with ui.row().classes('full-width gap-4 items-center justify-between'):
                        # Search input
                        with ui.row().classes('items-center gap-4 flex-grow'):
                            search_input = ui.input(
                                label='Search users',
                                placeholder='Search by username...'
                            ).classes('flex-grow')
                            search_input.on('update:model-value', lambda e: self._on_search_change(e.args))
                        
                        # Include inactive checkbox
                        with ui.row().classes('items-center gap-3'):
                            inactive_switch = ui.switch('Include Inactive', value=self.include_inactive)
                            inactive_switch.on('update:model-value', lambda e: self._on_filter_change(e.args))

                            # Refresh button
                            ui.button(
                                icon='refresh',
                                on_click=self._refresh_users
                            ).classes('btn').props('flat')

                            # Add user button
                            ui.button(
                                icon='person_add',
                                on_click=self._open_add_user
                            ).classes('btn btn-primary')
            
            # User table
            self.table_container = ui.column().classes('full-width')
            await self._refresh_users()
    
    async def _render_statistics(self):
        """Render user statistics cards."""
        # Load all users for statistics
        all_users = await self.user_service.get_all_users(self.current_user, include_inactive=True)

        stats = {
            'total': len(all_users),
            'active': len([u for u in all_users if u.is_active]),
            'admins': len([u for u in all_users if u.is_admin()]),
            'moderators': len([u for u in all_users if u.is_moderator() and not u.is_admin()]),
            'users': len([u for u in all_users if not u.is_moderator()]),
            'racetime_linked': len([u for u in all_users if u.racetime_id])
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

                    # RaceTime linked
                    with ui.column().classes('items-center'):
                        ui.label(str(stats['racetime_linked'])).classes('text-3xl font-bold')
                        ui.label('RaceTime Linked').classes('text-sm text-secondary')
    
    async def _refresh_users(self):
        """Refresh the user list."""
        try:
            # Load users based on current filters
            if self.search_query:
                self.users = await self.user_service.search_users(self.current_user, self.search_query)
                if not self.include_inactive:
                    self.users = [u for u in self.users if u.is_active]
            else:
                self.users = await self.user_service.get_all_users(self.current_user, include_inactive=self.include_inactive)
            
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
            
            # Create table using reusable component
            with ui.element('div').classes('card'):
                async def render_user_cell(u: User):
                    with ui.row().classes('items-center gap-2'):
                        if u.discord_avatar:
                            avatar_url = f"https://cdn.discordapp.com/avatars/{u.discord_id}/{u.discord_avatar}.png"
                            ui.image(avatar_url).classes('w-8 h-8 rounded-full')
                        else:
                            ui.icon('account_circle').classes('text-2xl')
                        ui.label(u.discord_username).classes('font-semibold')

                async def render_email_cell(u: User):
                    if u.discord_email:
                        ui.label(u.discord_email).classes('text-sm')
                    else:
                        ui.label('—').classes('text-secondary')

                async def render_permission_cell(u: User):
                    badge_class = 'badge-admin' if u.is_admin() else 'badge-moderator' if u.is_moderator() else 'badge-user'
                    with ui.element('span').classes(f'badge {badge_class}'):
                        ui.label(u.permission.name)

                async def render_status_cell(u: User):
                    status_class = 'badge-success' if u.is_active else 'badge-danger'
                    with ui.element('span').classes(f'badge {status_class}'):
                        ui.label('Active' if u.is_active else 'Inactive')

                async def render_racetime_cell(u: User):
                    if u.racetime_id:
                        with ui.column().classes('gap-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('link').classes('text-sm text-success')
                                ui.link(
                                    u.racetime_name,
                                    f'https://racetime.gg/user/{u.racetime_id}',
                                    new_tab=True
                                ).classes('text-sm')
                            # Can edit if self or admin with higher permission
                            can_edit = (self.current_user.id == u.id or 
                                       (self.current_user.has_permission(Permission.ADMIN) and 
                                        self.current_user.permission > u.permission))
                            if can_edit:
                                ui.button(
                                    'Unlink',
                                    icon='link_off',
                                    on_click=lambda x=u: self._unlink_racetime(x)
                                ).classes('btn btn-sm').props('flat size=sm color=negative')
                    else:
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('link_off').classes('text-sm text-secondary')
                            ui.label('Not linked').classes('text-sm text-secondary')

                async def render_actions_cell(u: User):
                    # Can edit if self or admin with higher permission
                    can_edit = (self.current_user.id == u.id or 
                               (self.current_user.has_permission(Permission.ADMIN) and 
                                self.current_user.permission > u.permission))
                    
                    with ui.row().classes('gap-1'):
                        if can_edit:
                            ui.button(
                                icon='edit',
                                on_click=lambda x=u: self._edit_user(x)
                            ).classes('btn btn-sm').props('flat')
                        else:
                            ui.button(
                                icon='edit'
                            ).classes('btn btn-sm').props('flat disable')

                columns = [
                    TableColumn(label='User', cell_render=render_user_cell),
                    TableColumn(label='Discord ID', key='discord_id', cell_classes='text-sm font-mono'),
                    TableColumn(label='Email', cell_render=render_email_cell),
                    TableColumn(label='Permission', cell_render=render_permission_cell),
                    TableColumn(label='Status', cell_render=render_status_cell),
                    TableColumn(label='RaceTime', cell_render=render_racetime_cell),
                    TableColumn(label='Actions', cell_render=render_actions_cell),
                ]

                table = ResponsiveTable(columns=columns, rows=self.users)
                await table.render()
    
    async def _render_user_row(self, _user: User):
        """Deprecated: Table row rendering is now handled by ResponsiveTable."""
        return
    
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

    async def _unlink_racetime(self, user: User):
        """
        Open unlink RaceTime dialog for user.

        Args:
            user: User to unlink RaceTime account from
        """
        dialog = RacetimeUnlinkDialog(
            user=user,
            admin_user=self.current_user,
            on_unlink=self._refresh_users
        )
        await dialog.show()

    async def _open_add_user(self):
        """Open dialog to add a new user and refresh on success."""
        dialog = UserAddDialog(
            current_user_permission=self.current_user.permission,
            on_save=self._refresh_users,
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
