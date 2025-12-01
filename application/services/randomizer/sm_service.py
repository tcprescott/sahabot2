"""
Super Metroid Randomizer (SM) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.sm.services instead.

This service handles generation of Super Metroid randomizer seeds via:
- VARIA randomizer (sm.samus.link API)
- DASH randomizer (dashrando.net API)
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.sm.services.sm_service import SMService, SMRandomizerType

__all__ = ["SMService", "SMRandomizerType"]
