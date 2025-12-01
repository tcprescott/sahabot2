"""
Tournament plugin repositories.

This module re-exports tournament-related repositories from the core application.
In a future phase, these repositories may be moved directly into the plugin.

For now, this provides a stable import path for plugin-internal use.
"""

from application.repositories.tournament_repository import TournamentRepository
from application.repositories.tournament_usage_repository import (
    TournamentUsageRepository,
)
from application.repositories.stream_channel_repository import StreamChannelRepository
from application.repositories.tournament_match_settings_repository import (
    TournamentMatchSettingsRepository,
)

__all__ = [
    "TournamentRepository",
    "TournamentUsageRepository",
    "StreamChannelRepository",
    "TournamentMatchSettingsRepository",
]
