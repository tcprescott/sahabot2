"""
A Link to the Past Randomizer (ALTTPR) service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.alttpr.services instead.

This service handles generation of ALTTPR seeds via the official API.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.alttpr.services.alttpr_service import ALTTPRService

__all__ = ["ALTTPRService"]
