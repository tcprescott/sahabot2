"""
Final Fantasy Randomizer (FFR) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.ffr.services instead.

This service handles generation of Final Fantasy randomizer seeds.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.ffr.services.ffr_service import FFRService

__all__ = ["FFRService"]
