"""
Views package for SahaBot2.

This package contains view modules for different sections of the application.
Each view module defines the content and layout for a specific page or tab.
"""

from views.overview import OverviewView
from views.schedule import ScheduleView
from views.users import UsersView
from views.reports import ReportsView
from views.settings import SettingsView
from views.favorites import FavoritesView
from views.tools import ToolsView
from views.help import HelpView
from views.about import AboutView
from views.archive import ArchiveView
from views.lorem_ipsum import LoremIpsumView

__all__ = [
    'OverviewView',
    'ScheduleView',
    'UsersView',
    'ReportsView',
    'SettingsView',
    'FavoritesView',
    'ToolsView',
    'HelpView',
    'AboutView',
    'ArchiveView',
    'LoremIpsumView',
]
