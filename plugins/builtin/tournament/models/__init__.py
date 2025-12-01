"""
Tournament plugin models.

This module exports tournament-related models defined in the plugin.
"""

from plugins.builtin.tournament.models.match_schedule import (
    Tournament,
    Match,
    MatchPlayers,
    MatchSeed,
    TournamentPlayers,
    StreamChannel,
    Crew,
    CrewRole,
    DiscordEventFilter,
)
from plugins.builtin.tournament.models.tournament_match_settings import (
    TournamentMatchSettings,
)
from plugins.builtin.tournament.models.tournament_usage import TournamentUsage

# Database models (returned by plugin.get_models())
__all__ = [
    # Database models
    "Tournament",
    "Match",
    "MatchPlayers",
    "MatchSeed",
    "TournamentPlayers",
    "StreamChannel",
    "Crew",
    "TournamentMatchSettings",
    "TournamentUsage",
    # Enums (not registered as models, but useful for imports)
    "CrewRole",
    "DiscordEventFilter",
]
