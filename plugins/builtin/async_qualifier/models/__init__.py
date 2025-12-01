"""
AsyncQualifier plugin models.

Models are defined in the core application at models.async_tournament and
are re-exported here for convenience within the plugin. Models remain in
the core because they are tied to database migrations via Tortoise ORM.

Usage:
    from plugins.builtin.async_qualifier.models import AsyncQualifier
    # or directly from core:
    from models.async_tournament import AsyncQualifier
"""

from models.async_tournament import (
    AsyncQualifier,
    AsyncQualifierPool,
    AsyncQualifierPermalink,
    AsyncQualifierRace,
    AsyncQualifierLiveRace,
    AsyncQualifierAuditLog,
)

__all__ = [
    # Database models
    "AsyncQualifier",
    "AsyncQualifierPool",
    "AsyncQualifierPermalink",
    "AsyncQualifierRace",
    "AsyncQualifierLiveRace",
    "AsyncQualifierAuditLog",
]
