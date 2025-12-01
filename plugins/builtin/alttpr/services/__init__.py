"""
Services for the ALTTPR plugin.

This module provides ALTTPR-related services.
"""

from plugins.builtin.alttpr.services.alttpr_service import ALTTPRService

# Note: ALTTPRMysteryService remains in application/services/randomizer/
# due to its dependency on ALTTPRService and potential circular import issues.
# Use the following import for mystery service:
# from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService

__all__ = [
    "ALTTPRService",
]
