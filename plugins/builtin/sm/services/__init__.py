"""
Services for the SM plugin.

This module provides SM-related services.
"""

from plugins.builtin.sm.services.sm_service import SMService
from plugins.builtin.sm.services.sm_defaults import (
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
