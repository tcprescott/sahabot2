"""
Home views package.

Views used by the home page.
"""

from views.home.overview import OverviewView
from views.home.schedule import ScheduleView
from views.home.users import UsersView
from views.home.reports import ReportsView
from views.home.settings import SettingsView
from views.home.favorites import FavoritesView
from views.home.tools import ToolsView
from views.home.help import HelpView
from views.home.about import AboutView
from views.home.welcome import WelcomeView
from views.home.archive import ArchiveView
from views.home.lorem_ipsum import LoremIpsumView

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
    'WelcomeView',
    'ArchiveView',
    'LoremIpsumView',
]
