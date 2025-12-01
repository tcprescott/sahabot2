"""
SMZ3 (Super Metroid/ALTTP Combo) Randomizer service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.smz3.services instead.

This service handles generation of SMZ3 combo randomizer seeds via samus.link API.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.smz3.services.smz3_service import (
    SMZ3Service,
    DEFAULT_SMZ3_SETTINGS,
)

__all__ = ["SMZ3Service", "DEFAULT_SMZ3_SETTINGS"]
