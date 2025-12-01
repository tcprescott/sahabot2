"""
Services for the FFR plugin.

This module re-exports FFR-related services from the core application.
"""

from application.services.randomizer.ffr_service import FFRService

__all__ = [
    "FFRService",
]
