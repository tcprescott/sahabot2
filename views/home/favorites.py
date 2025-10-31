"""
Favorites view for bookmarked items and quick access.

Displays saved items, frequent actions, and personalized shortcuts.
"""

from nicegui import ui
from components import Card
from models import User


class FavoritesView:
    """Favorites view with bookmarked content."""
    
    @staticmethod
    async def render(user: User):
        """
        Render the favorites tab content.
        
        Args:
            user: Current authenticated user
        """
        with ui.column().classes('full-width gap-md'):
            # Favorites overview card
            Card.simple(
                title='Your Favorites',
                description='Quick access to your bookmarked items, frequently used features, and personalized shortcuts for faster navigation.'
            )
            
            # Add favorite card
            Card.action(
                title='Add to Favorites',
                description='Bookmark pages, actions, or items for quick access.',
                button_text='Add Favorite',
                on_click=lambda: ui.notify('Add favorite dialog would open here')
            )
            
            # Favorites summary card
            Card.info(
                title='Favorites Summary',
                items=[
                    ('Total Bookmarks', '8'),
                    ('Most Accessed', 'User Management'),
                    ('Recently Added', 'Reports Dashboard'),
                    ('Categories', '4')
                ]
            )
