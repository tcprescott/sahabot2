"""
Help view for documentation and support.

Provides access to help resources, documentation, and support channels.
"""

from nicegui import ui
from components import Card
from models import User


class HelpView:
    """Help view with documentation content."""
    
    @staticmethod
    async def render(user: User):
        """
        Render the help tab content.
        
        Args:
            user: Current authenticated user
        """
        with ui.column().classes('full-width gap-md'):
            # Help overview card
            Card.simple(
                title='Help & Documentation',
                description='Find answers to common questions, browse documentation, and get support for using SahaBot2 effectively.'
            )
            
            # Contact support card
            Card.action(
                title='Contact Support',
                description='Need help? Reach out to our support team for assistance.',
                button_text='Get Support',
                on_click=lambda: ui.notify('Support contact form would open here')
            )
            
            # Help resources card
            Card.info(
                title='Help Resources',
                items=[
                    ('Documentation', 'Available'),
                    ('Video Tutorials', '15 videos'),
                    ('FAQ Articles', '42'),
                    ('Support Status', 'Online')
                ]
            )
