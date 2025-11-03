"""
Overview view for the SahaBot2 home page.

Displays dashboard statistics, quick actions, and system status.
"""

from nicegui import ui
from components import Card
from models import User
from views.home.recent_tournaments import RecentTournamentsView


class OverviewView:
    """Overview view with dashboard content."""
    
    @staticmethod
    async def render(user: User):
        """
        Render the overview tab content.
        
        Args:
            user: Current authenticated user
        """
        with ui.column().classes('full-width gap-md'):
            # Welcome card
            Card.simple(
                title='Welcome to SahaBot2',
                description=f'Hello, {user.discord_username}! This is your personalized dashboard with quick access to key features and system information.'
            )
            
            # Quick actions card
            Card.action(
                title='Quick Actions',
                description='Access frequently used features and tools.',
                button_text='View All Actions',
                on_click=lambda: ui.notify('Actions clicked!')
            )
            
            # System status card
            Card.info(
                title='System Status',
                items=[
                    ('Status', 'Online'),
                    ('Uptime', '99.9%'),
                    ('Active Users', '42'),
                    ('Permission Level', user.permission.name)
                ]
            )
            
            # Recent tournaments
            recent_view = RecentTournamentsView(user)
            await recent_view.render()
