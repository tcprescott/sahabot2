"""
Handlers for the SM plugin.

This module exports the RaceTime.gg handler for Super Metroid.
"""

# Re-export from core handlers for backwards compatibility
from racetime.handlers.sm_race_handler import SMRaceHandler

__all__ = [
    "SMRaceHandler",
]
