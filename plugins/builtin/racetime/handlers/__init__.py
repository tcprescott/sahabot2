"""
RaceTime Plugin handlers.

This module re-exports race handlers from the core application
to provide a unified interface through the plugin system.
"""

from racetime.handlers.base_handler import SahaRaceHandler

__all__ = [
    "SahaRaceHandler",
]
