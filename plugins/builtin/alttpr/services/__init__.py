"""
Services for the ALTTPR plugin.

This module re-exports ALTTPR-related services from the core application
for backwards compatibility and provides a unified import interface.
"""

# Re-export from core services for backwards compatibility
from application.services.randomizer.alttpr_service import ALTTPRService
from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService

__all__ = [
    "ALTTPRService",
    "ALTTPRMysteryService",
]
