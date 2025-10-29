"""
Users view for managing user accounts and permissions.

Displays user list, allows editing permissions, and manages user settings.
"""

from nicegui import ui
from components import Card
from models import User


class UsersView:
    """Users view with user management content."""
    
    @staticmethod
    async def render(user: User):
        """
        Render the users tab content.
        
        Args:
            user: Current authenticated user
        """
        with ui.column().classes('full-width gap-md'):
            # User management card
            Card.simple(
                title='User Management',
                description='Manage user accounts, permissions, and settings. View user activity and configure access levels across the system.'
            )
            
            # Add user card
            Card.action(
                title='Add New User',
                description='Invite new users to the platform with customizable permissions.',
                button_text='Invite User',
                on_click=lambda: ui.notify('User invitation dialog would open here')
            )
            
            # User statistics card
            Card.info(
                title='User Statistics',
                items=[
                    ('Total Users', '142'),
                    ('Active Today', '38'),
                    ('Admins', '5'),
                    ('Moderators', '12')
                ]
            )
