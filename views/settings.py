"""
Settings view for application and user configuration.

Allows users to configure preferences, notifications, and system settings.
"""

from nicegui import ui
from components import Card
from models import User


class SettingsView:
    """Settings view with configuration content."""
    
    @staticmethod
    async def render(user: User):
        """
        Render the settings tab content.
        
        Args:
            user: Current authenticated user
        """
        with ui.column().classes('full-width gap-md'):
            # Settings overview card
            Card.simple(
                title='Application Settings',
                description='Configure your preferences, notification settings, privacy options, and customize your experience with SahaBot2.'
            )
            
            # Account settings card
            Card.action(
                title='Account Settings',
                description='Manage your account details, security, and linked services.',
                button_text='Edit Account',
                on_click=lambda: ui.notify('Account settings would open here')
            )
            
            # Current preferences card
            Card.info(
                title='Current Preferences',
                items=[
                    ('Theme', 'Auto (System)'),
                    ('Notifications', 'Enabled'),
                    ('Language', 'English'),
                    ('Timezone', 'UTC-5')
                ]
            )
