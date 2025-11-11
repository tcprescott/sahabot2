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

# Available handler classes for RaceTime bots
# These correspond to the handler classes in this package
AVAILABLE_HANDLER_CLASSES = [
    "SahaRaceHandler",  # Default base handler with common commands
    "ALTTPRRaceHandler",  # A Link to the Past Randomizer handler
    "SMRaceHandler",  # Super Metroid handler
    "SMZ3RaceHandler",  # SMZ3 (Super Metroid + ALTTP combo) handler
    "AsyncLiveRaceHandler",  # Async tournament live race handler
]

__all__ = [
    "RacetimeBot",
    "SahaRaceHandler",
    "get_racetime_bot_instance",
    "get_all_racetime_bot_instances",
    "start_racetime_bot",
    "stop_racetime_bot",
    "stop_all_racetime_bots",
    "AVAILABLE_HANDLER_CLASSES",
]
