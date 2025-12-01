"""
Default settings and configuration for Super Metroid randomizers.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.sm.services.sm_defaults instead.

This module provides shared default settings for VARIA and DASH randomizers
used across Discord commands and RaceTime.gg handlers.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.sm.services.sm_defaults import (
    VARIA_DEFAULTS,
    DASH_DEFAULTS,
    get_varia_settings,
    get_dash_settings,
)

__all__ = [
    "VARIA_DEFAULTS",
    "DASH_DEFAULTS",
    "get_varia_settings",
    "get_dash_settings",
]
