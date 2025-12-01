"""
Aria of Sorrow Randomizer (AOSR) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.aosr.services instead.

This service handles generation of Castlevania: Aria of Sorrow randomizer seeds.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.aosr.services.aosr_service import AOSRService

__all__ = ["AOSRService"]
