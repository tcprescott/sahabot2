"""
About view for application information.

Displays app version, credits, license, and system information.
"""

from nicegui import ui
from components import Card
from models import User


class AboutView:
    """About view with application information."""
    
    @staticmethod
    async def render(user: User):
        """
        Render the about tab content.
        
        Args:
            user: Current authenticated user
        """
        with ui.column().classes('full-width gap-md'):
            # About overview card
            Card.simple(
                title='About SahaBot2',
                description='SahaBot2 is a modern web application built with NiceGUI and FastAPI, featuring Discord OAuth2 authentication and comprehensive user management.'
            )
            
            # Check for updates card
            Card.action(
                title='Updates',
                description='Check for the latest version and view release notes.',
                button_text='Check Updates',
                on_click=lambda: ui.notify('Checking for updates...')
            )
            
            # Version info card
            Card.info(
                title='Version Information',
                items=[
                    ('Version', '2.0.0'),
                    ('Build Date', '2024-01-15'),
                    ('Python', '3.11+'),
                    ('License', 'MIT')
                ]
            )
