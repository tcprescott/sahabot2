"""
Services for the ALTTPR plugin.

This module provides ALTTPR-related services.
"""

from plugins.builtin.alttpr.services.alttpr_service import ALTTPRService
from plugins.builtin.alttpr.services.alttpr_mystery_service import ALTTPRMysteryService

__all__ = [
    "ALTTPRService",
    "ALTTPRMysteryService",
]
