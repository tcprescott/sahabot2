"""
Services for the SM plugin.

This module re-exports SM-related services from the core application
for backwards compatibility and provides a unified import interface.
"""

# Re-export from core services for backwards compatibility
from application.services.randomizer.sm_service import SMService
from application.services.randomizer.sm_defaults import (
    VARIA_DEFAULTS,
    DASH_DEFAULTS,
    get_varia_settings,
    get_dash_settings,
)

__all__ = [
    "SMService",
    "VARIA_DEFAULTS",
    "DASH_DEFAULTS",
    "get_varia_settings",
    "get_dash_settings",
]
