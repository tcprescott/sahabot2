"""
Services for the SMZ3 plugin.

This module re-exports SMZ3-related services from the core application
for backwards compatibility and provides a unified import interface.
"""

# Re-export from core services for backwards compatibility
from application.services.randomizer.smz3_service import (
    SMZ3Service,
    DEFAULT_SMZ3_SETTINGS,
)

__all__ = [
    "SMZ3Service",
    "DEFAULT_SMZ3_SETTINGS",
]
