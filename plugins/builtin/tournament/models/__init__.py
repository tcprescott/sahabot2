"""
Tournament plugin models.

This module re-exports tournament-related models from the core application.
In a future phase, these models may be moved directly into the plugin.

For now, this provides a stable import path for plugin-internal use.
"""

from models.match_schedule import (
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
from models.tournament_match_settings import TournamentMatchSettings

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
    # Enums (not registered as models, but useful for imports)
    "CrewRole",
    "DiscordEventFilter",
]
