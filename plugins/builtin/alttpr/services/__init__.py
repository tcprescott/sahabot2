"""
Services for the ALTTPR plugin.

This module provides ALTTPR-related services.
"""

from plugins.builtin.alttpr.services.alttpr_service import ALTTPRService

# Re-export mystery service from core for now - needs separate migration
from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService

__all__ = [
    "ALTTPRService",
    "ALTTPRMysteryService",
]
