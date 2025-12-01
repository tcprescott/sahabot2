"""
SpeedGaming Plugin services.

This module provides SpeedGaming-related services.
"""

from plugins.builtin.speedgaming.services.speedgaming_service import (
    SpeedGamingService,
    SpeedGamingEpisode,
    SpeedGamingEvent,
    SpeedGamingMatch,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
    SpeedGamingChannel,
)
from plugins.builtin.speedgaming.services.speedgaming_etl_service import (
    SpeedGamingETLService,
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
