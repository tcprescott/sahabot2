"""
SpeedGaming integration services.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.speedgaming.services instead.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.speedgaming.services import (
    SpeedGamingService,
    SpeedGamingETLService,
    SpeedGamingEpisode,
    SpeedGamingEvent,
    SpeedGamingMatch,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
    SpeedGamingChannel,
)

__all__ = [
    "SpeedGamingService",
    "SpeedGamingETLService",
    "SpeedGamingEpisode",
    "SpeedGamingEvent",
    "SpeedGamingMatch",
    "SpeedGamingPlayer",
    "SpeedGamingCrewMember",
    "SpeedGamingChannel",
]
