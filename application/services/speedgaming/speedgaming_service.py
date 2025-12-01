"""
SpeedGaming API service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.speedgaming.services instead.

This service handles API calls to SpeedGaming.org for fetching episode and event data.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.speedgaming.services.speedgaming_service import (
    SpeedGamingService,
    SpeedGamingEpisode,
    SpeedGamingEvent,
    SpeedGamingMatch,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
    SpeedGamingChannel,
)

__all__ = [
    "SpeedGamingService",
    "SpeedGamingEpisode",
    "SpeedGamingEvent",
    "SpeedGamingMatch",
    "SpeedGamingPlayer",
    "SpeedGamingCrewMember",
    "SpeedGamingChannel",
]
