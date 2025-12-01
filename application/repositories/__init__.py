"""
Application repositories package.

This package contains all repository classes for data access.
Tournament repositories are now in the tournament plugin and re-exported here
for backward compatibility.
"""

from application.repositories.user_repository import UserRepository
from application.repositories.audit_repository import AuditRepository

# Re-export tournament repositories from the plugin for backward compatibility
from plugins.builtin.tournament.repositories import (
    TournamentRepository,
    TournamentUsageRepository,
    StreamChannelRepository,
    TournamentMatchSettingsRepository,
)

__all__ = [
    "UserRepository",
    "AuditRepository",
    # Tournament repositories (from plugin)
    "TournamentRepository",
    "TournamentUsageRepository",
    "StreamChannelRepository",
    "TournamentMatchSettingsRepository",
]
