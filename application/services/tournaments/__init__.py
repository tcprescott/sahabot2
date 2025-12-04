"""Tournament management services (deprecated path).

This package now re-exports tournament services from
``modules.tournament.services``. Prefer importing from the new module path.
"""

from modules.tournament.services import (  # type: ignore F401
    TournamentService,
    TournamentUsageService,
    StreamChannelService,
    TournamentMatchSettingsService,
    PresetSelectionService,
)

__all__ = [
    "TournamentService",
    "TournamentUsageService",
    "StreamChannelService",
    "TournamentMatchSettingsService",
    "PresetSelectionService",
]
