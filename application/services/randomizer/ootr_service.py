"""
Ocarina of Time Randomizer (OOTR) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.ootr.services instead.

This service handles generation of Ocarina of Time randomizer seeds via API.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.ootr.services.ootr_service import OOTRService

__all__ = ["OOTRService"]
