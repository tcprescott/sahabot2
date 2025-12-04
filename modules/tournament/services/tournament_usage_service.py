"""
Service for tournament usage tracking.

This service handles business logic for tracking which tournaments users access.
"""

import logging
from models import User, Tournament
from modules.tournament.repositories.tournament_usage_repository import (
    TournamentUsageRepository,
)

logger = logging.getLogger(__name__)


class TournamentUsageService:
    """Service for tournament usage tracking operations."""

    def __init__(self):
        """Initialize service with repository."""
        self.repository = TournamentUsageRepository()

    async def track_tournament_access(
        self,
        user: User,
        tournament: Tournament,
        organization_id: int,
        organization_name: str,
    ) -> None:
        """
        Track that a user accessed a tournament.

        This updates or creates a usage record with the current timestamp.
        Should be called whenever a user views tournament details or interacts with it.

        Args:
            user: User accessing the tournament
            tournament: Tournament being accessed
            organization_id: ID of the organization
            organization_name: Name of the organization
        """
        await self.repository.record_usage(
            user=user,
            tournament=tournament,
            organization_id=organization_id,
            organization_name=organization_name,
        )

        logger.debug(
            "Tracked tournament access: user=%s, tournament=%s",
            user.discord_username,
            tournament.name,
        )

    async def get_recent_tournaments(self, user: User, limit: int = 5) -> list[dict]:
        """
        Get user's recently accessed tournaments.

        Returns a list of tournament info with organization context.

        Authorization: Users can only view their own tournament history
        (enforced by user parameter scoping in repository query).

        Args:
            user: User to fetch history for
            limit: Maximum number of tournaments to return (default 5)

        Returns:
            list[dict]: Recent tournaments with organization info
        """
        usages = await self.repository.get_recent_tournaments(user, limit)

        # Convert to dict for easy display
        result = []
        for usage in usages:
            result.append(
                {
                    "tournament_id": usage.tournament_id,
                    "tournament_name": usage.tournament_name,
                    "organization_id": usage.organization_id,
                    "organization_name": usage.organization_name,
                    "last_accessed": usage.last_accessed,
                }
            )

        return result

    async def cleanup_old_usage(self, days_to_keep: int = 90) -> int:
        """
        Remove tournament usage entries older than specified days.

        This should be called periodically (e.g., daily) to prevent table bloat.

        Args:
            days_to_keep: Number of days to keep entries (default 90)

        Returns:
            int: Number of records deleted
        """
        deleted_count = await self.repository.cleanup_old_entries(days_to_keep)

        logger.info(
            "Cleanup completed: removed %d old tournament usage entries", deleted_count
        )

        return deleted_count

    async def cleanup_excess_usage(self, keep_per_user: int = 10) -> int:
        """
        Remove excess tournament usage entries per user.

        Keeps only the most recent N tournaments per user.
        This should be called periodically to prevent table bloat.

        Args:
            keep_per_user: Number of most recent entries to keep per user (default 10)

        Returns:
            int: Number of records deleted
        """
        deleted_count = await self.repository.cleanup_excess_per_user(keep_per_user)

        logger.info(
            "Cleanup completed: removed %d excess tournament usage entries",
            deleted_count,
        )

        return deleted_count
