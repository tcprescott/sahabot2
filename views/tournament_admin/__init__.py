"""
Tournament admin views.

Views for managing tournament-specific settings and content.
"""

from views.tournament_admin.tournament_overview import TournamentOverviewView
from views.tournament_admin.tournament_matches import TournamentMatchesView
from views.tournament_admin.tournament_players import TournamentPlayersView
from views.tournament_admin.tournament_racetime_settings import TournamentRacetimeSettingsView
from views.tournament_admin.tournament_settings import TournamentSettingsView

__all__ = [
    'TournamentOverviewView',
    'TournamentMatchesView',
    'TournamentPlayersView',
    'TournamentRacetimeSettingsView',
    'TournamentSettingsView',
]
