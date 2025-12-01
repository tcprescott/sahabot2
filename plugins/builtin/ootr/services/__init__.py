"""
Services for the OOTR plugin.

This module re-exports OOTR-related services from the core application
for backwards compatibility and provides a unified import interface.
"""

# Re-export from core services for backwards compatibility
from application.services.randomizer.ootr_service import OOTRService

__all__ = [
    "OOTRService",
]
