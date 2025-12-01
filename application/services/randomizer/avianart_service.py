"""
Avianart randomizer service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.avianart.services instead.

This service handles generation of ALTTPR door randomizer seeds via the
Avianart API (Hi, I'm Cody's door randomizer generator).
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.avianart.services.avianart_service import AvianartService

__all__ = ["AvianartService"]
