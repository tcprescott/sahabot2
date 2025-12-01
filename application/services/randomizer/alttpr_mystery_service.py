"""
A Link to the Past Randomizer Mystery service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.alttpr.services instead.

This service handles generation of mystery seeds with weighted preset selection.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.alttpr.services.alttpr_mystery_service import ALTTPRMysteryService

__all__ = ["ALTTPRMysteryService"]
