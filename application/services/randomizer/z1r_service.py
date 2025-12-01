"""
Zelda 1 Randomizer (Z1R) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.z1r.services instead.

This service handles generation of The Legend of Zelda randomizer seeds.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.z1r.services.z1r_service import Z1RService

__all__ = ["Z1RService"]
