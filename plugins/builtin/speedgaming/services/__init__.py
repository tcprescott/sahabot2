"""
SpeedGaming Plugin services.

This module re-exports SpeedGaming-related services from the core application
to provide a unified interface through the plugin system.
"""

from application.services.speedgaming.speedgaming_service import (
    SpeedGamingService,
    SpeedGamingEpisode,
    SpeedGamingEvent,
    SpeedGamingMatch,
    SpeedGamingPlayer,
    SpeedGamingCrewMember,
    SpeedGamingChannel,
)
from application.services.speedgaming.speedgaming_etl_service import (
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
