"""
Tournament views package.

Views for tournament-related pages.
"""

from views.tournaments.tournament_org_select import TournamentOrgSelectView
from views.tournaments.event_schedule import EventScheduleView
from views.tournaments.my_matches import MyMatchesView
from views.tournaments.my_settings import MySettingsView
from views.tournaments.tournament_management import TournamentManagementView
from views.tournaments.async_dashboard import AsyncDashboardView
from views.tournaments.async_leaderboard import AsyncLeaderboardView
from views.tournaments.async_pools import AsyncPoolsView
from views.tournaments.async_player_history import AsyncPlayerHistoryView
from views.tournaments.async_permalink import AsyncPermalinkView
from views.tournaments.async_review_queue import AsyncReviewQueueView
from views.tournaments.async_live_races import AsyncLiveRacesView

__all__ = [
    "TournamentOrgSelectView",
    "EventScheduleView",
    "MyMatchesView",
    "MySettingsView",
    "TournamentManagementView",
    "AsyncDashboardView",
    "AsyncLeaderboardView",
    "AsyncPoolsView",
    "AsyncPlayerHistoryView",
    "AsyncPermalinkView",
    "AsyncReviewQueueView",
    "AsyncLiveRacesView",
]
