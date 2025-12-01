"""
Handlers for the ALTTPR plugin.

This module exports the RaceTime.gg handler for ALTTPR.
"""

# Re-export from core handlers for backwards compatibility
from racetime.handlers.alttpr_handler import ALTTPRHandler

__all__ = [
    "ALTTPRHandler",
]
