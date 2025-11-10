"""
Tournament admin views.

Views for managing tournament-specific settings and content.
"""

from views.tournament_admin.tournament_overview import TournamentOverviewView
from views.tournament_admin.tournament_players import TournamentPlayersView
from views.tournament_admin.tournament_racetime_settings import (
    TournamentRacetimeSettingsView,
)
from views.tournament_admin.tournament_discord_events import TournamentDiscordEventsView
from views.tournament_admin.tournament_settings import TournamentSettingsView
from views.tournament_admin.tournament_randomizer_settings import (
    TournamentRandomizerSettingsView,
)

__all__ = [
    "TournamentOverviewView",
    "TournamentPlayersView",
    "TournamentRacetimeSettingsView",
    "TournamentDiscordEventsView",
    "TournamentSettingsView",
    "TournamentRandomizerSettingsView",
]
