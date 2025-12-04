"""Tournament admin views."""

from .tournament_discord_events import TournamentDiscordEventsView
from .tournament_overview import TournamentOverviewView
from .tournament_players import TournamentPlayersView
from .tournament_racetime_settings import TournamentRacetimeSettingsView
from .tournament_randomizer_settings import TournamentRandomizerSettingsView
from .tournament_settings import TournamentSettingsView
from .tournament_preset_selection_rules import TournamentPresetSelectionRulesView

__all__ = [
    "TournamentOverviewView",
    "TournamentPlayersView",
    "TournamentRacetimeSettingsView",
    "TournamentDiscordEventsView",
    "TournamentSettingsView",
    "TournamentRandomizerSettingsView",
    "TournamentPresetSelectionRulesView",
]
