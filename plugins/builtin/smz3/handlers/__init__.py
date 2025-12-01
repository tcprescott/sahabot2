"""
Handlers for the SMZ3 plugin.

This module exports the RaceTime.gg handler for SMZ3.
"""

# Re-export from core handlers for backwards compatibility
from racetime.handlers.smz3_race_handler import SMZ3RaceHandler

__all__ = [
    "SMZ3RaceHandler",
]
