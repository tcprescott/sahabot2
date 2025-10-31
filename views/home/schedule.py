"""
Schedule view for managing events and calendar.

Displays upcoming events, allows scheduling, and provides calendar integration.
"""

from nicegui import ui
from components import Card
from models import User


class ScheduleView:
    """Schedule view with event management content."""
    
    @staticmethod
    async def render(user: User):
        """
        Render the schedule tab content.
        
        Args:
            user: Current authenticated user
        """
        with ui.column().classes('full-width gap-md'):
            # Schedule overview card
            Card.simple(
                title='Event Schedule',
                description='View and manage your upcoming events, meetings, and deadlines. Stay organized with calendar integration and reminders.'
            )
            
            # Create event card
            Card.action(
                title='Create New Event',
                description='Add a new event to your schedule with custom notifications.',
                button_text='New Event',
                on_click=lambda: ui.notify('Create event dialog would open here')
            )
            
            # Upcoming events card
            Card.info(
                title='Upcoming Events',
                items=[
                    ('Next Event', 'Team Meeting - Tomorrow 2pm'),
                    ('This Week', '5 events'),
                    ('This Month', '18 events'),
                    ('Pending RSVPs', '3')
                ]
            )
