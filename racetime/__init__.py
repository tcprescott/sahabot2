"""
Racetime.gg bot integration package.

This package contains the racetime.gg bot implementation.
"""

from .client import (
    RacetimeBot,
    SahaRaceHandler,
    get_racetime_bot_instance,
    get_all_racetime_bot_instances,
    start_racetime_bot,
    stop_racetime_bot,
    stop_all_racetime_bots,
)

__all__ = [
    "RacetimeBot",
    "SahaRaceHandler",
    "get_racetime_bot_instance",
    "get_all_racetime_bot_instances",
    "start_racetime_bot",
    "stop_racetime_bot",
    "stop_all_racetime_bots",
]
